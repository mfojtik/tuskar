<%def name="render()">\
                #!/usr/bin/env python

                from novaclient.v1_1 import client
                from commands import getstatusoutput
                from time import sleep
                from os import environ
                import subprocess

                # Import keystone configuration
                #
                command = ['bash', '-c', 'source /root/stackrc && env']

                proc = subprocess.Popen(command, stdout=subprocess.PIPE)

                for line in proc.stdout:
                    (key, _, value) = line.partition("=")
                    environ[key] = value

                proc.communicate()


                def wait_for(loops, sleeptime, cmd):
                    i = 0
                    while i < loops:
                        (status, _) = getstatusoutput(cmd)
                        if status == 0:
                            return True
                        else:
                            sleep(sleeptime)
                            i = i + 1
                    return False


                def nova_client():
                    return client.Client(environ['OS_USERNAME'],
                            environ['OS_PASSWORD'],
                            environ['OS_TENANT_NAME'],
                            environ['OS_AUTH_URL'],
                            service_type="compute")


                def main():
                    # Wait for Nova Compute service to come up
                    wait_for(60, 10, 'test -f /opt/stack/boot-stack.ok')
                    wait_for(60, 10, 'nova list')

                    # We must enable host aggregate matching when scheduling
                    with open("/etc/nova/nova.conf", "a") as nova_conf:
                        nova_conf.write('scheduler_default_filters=' +
                                'AggregateInstanceExtraSpecsFilter,AvailabilityZoneFilter' +
                                ',RamFilter,ComputeFilter')

                    # Reload nova-scheduler configuration
                    getstatusoutput('service nova-scheduler reload')

                    # Remove default Nova flavors
                    for flavor_id in 5:
                        nova_client().flavors.delete(flavor_id)


                main()
