from subprocess import CalledProcessError


class CommandNotFoundOnImageError(CalledProcessError):
    def __init__(self, prior_error: CalledProcessError, command_name: str):
        super(CommandNotFoundOnImageError, self).__init__(
            prior_error.returncode,
            prior_error.cmd
        )
        self.command_name = command_name

    def __str__(self):
        return f"Command '{self.command_name}' was run, but is not " + \
            "present on the Docker image."
