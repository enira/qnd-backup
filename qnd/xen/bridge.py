import paramiko
import logging

logging.getLogger("paramiko").setLevel(logging.WARNING)

class Bridge:
    """
    Bridge between API and Xen. This class uses SSH to connect to the Xen server.
    """

    username = None
    password = None
    address = None

    _ssh = None
    
    def __init__(self, address, username, password):
        """
        Initialize the class
        """

        self.address = address
        self.username = username
        self.password = password
        self._ssh = None

    def disconnect(self):
        """
        Disconnect SSH session
        """
        if self._ssh != None:
            self._ssh.close()

    def connect(self):
        """
        Connect to session
        """
        self.connection()

    def connection(self):
        """
        Create a connection, set ssh paramiko to self signed keys
        """
        if not self.is_connected():
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self._ssh.connect(self.address, username=self.username, password=self.password)
        return self._ssh

    def is_connected(self):
        """
        Check if ssh is connected
        """
        transport = self._ssh.get_transport() if self._ssh else None
        return transport and transport.is_active()

    def command(self, cmd):
        """
        Run a command
        """
        result = []
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = self.connection().exec_command(cmd)
            exit_status = ssh_stdout.channel.recv_exit_status()  # Blocking call

            lines = ssh_stdout.read().splitlines()
            for line in lines:
                result.append(line)

            return result
        except Exception as e:
            print e

    def command_single(self, cmd):
        """
        Run a command with a single output
        """
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = self.connection().exec_command(cmd)
            exit_status = ssh_stdout.channel.recv_exit_status()  # Blocking call

            lst = ssh_stdout.read().splitlines()

            result = self._internal_parse_params(lst)

            return result

        except Exception as e:
            print e

    def command_array(self, cmd):
        """
        Run a command with multiple output
        """
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = self.connection().exec_command(cmd)
            exit_status = ssh_stdout.channel.recv_exit_status()  # Blocking call

            lst = ssh_stdout.read().splitlines()

            result = []
            lsts = [[]]
            lastline = None

            index = 0
            for line in lst:
                lsts[index].append(line)

                if line == '' and lastline == '':
                    index = index + 1
                    lsts.append([])

                lastline = line


            for l in lsts:
                if len(l) > 0:
                    result.append(self._internal_parse_params(l))

            return result

        except Exception as e:
            print e
    

    def _internal_parse_params(self, lines):
        """
        Parse command output
        """
        result = {}

        for line in lines:
            csv = line.split(':')

            if len(csv) >= 2:
                key = csv[0].split('(')[0].strip()
                value = csv[1].strip()

                result[key] = value
            else:
                pass
        return result
