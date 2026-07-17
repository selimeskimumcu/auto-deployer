from dataclasses import dataclass

import paramiko



class SSHConnectionError(Exception):
    pass



@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


def run_command(
        client: paramiko.SSHClient,
        command: str,
        timeout: int=15,
) -> CommandResult:
    _, stdout, stderr = client.exec_command(
        command,
        timeout=timeout,
    )

    exit_code = stdout.channel.recv_exit_status()

    return CommandResult(
        exit_code = exit_code,
        stdout=stdout.read().decode("utf-8", errors="replace").strip(),
        stderr=stderr.read().decode("utf-8", errors="replace").strip(),
    )

def test_ssh_connection(
        host: str,
        port: int,
        username: str,
        password: str,
) -> dict[str, object]:
    client = paramiko.SSHClient()

    client.load_system_host_keys()

    client.set_missing_host_key_policy(
        paramiko.RejectPolicy()
    )

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=10,
            banner_timeout=10,
            auth_timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

        hostname_result = run_command(
            client,
            "hostname",
        )

        username_result = run_command(
            client,
            "whoami",
        )

        operating_system_result = run_command(
            client,
            (
                 "if [ -f /etc/os-release ]; then "
                ". /etc/os-release && echo \"$PRETTY_NAME\"; "
                "else uname -srm; fi"
            ),
        )

        docker_version_result = run_command(
            client,
            "docker --version",
        )

        docker_access_result = run_command(
            client,
            "docker info >/dev/null 2>&1",
        )

        docker_installed = docker_version_result.exit_code == 0
        docker_accessible = docker_access_result.exit_code == 0

        return {
            "connected" : True,
            "hostname": hostname_result.stdout or None,
            "remote_username": username_result.stdout or None,
            "operating_system": operating_system_result.stdout or None,
            "docker_installed": docker_installed,
            "docker version": (
                docker_version_result.stdout
                if docker_installed
                else None
            ),
            "docker_accessible" : docker_accessible,
            "message" : "SSH bağlantısı başarıyla kuruldu.",
        }
    
    except paramiko.AuthenticationException as error:
        raise SSHConnectionError(
            "SSH kullanıcı adı veya parola hatalı."
        ) from error
    
    except paramiko.BadHostKeyException as error:
        raise SSHConnectionError(
            "sunucunun SSH host key bilgisi beklenen değerle uyuşmamaktadır."
        ) from error
    
    except paramiko.SSHException as error:
        raise SSHConnectionError(
            f"SSH bağlantısı kurulamadı: {error}"
        ) from error
    

    except TimeoutError as error:
        raise SSHConnectionError(
            "SSH bağlantısı zaman aşımına uğradı."
        ) from error
    
    except OSError as error:
        raise SSHConnectionError(
            f"sunucuya ağ bağlantısı kurulamadı: {error}"
        ) from error
    
    finally:
        client.close()