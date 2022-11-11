from qm import qua


class ExpVar:
    def __init__(
        self,
        name: str,
        var_type: type,
        create_stream: bool = True,
        is_adc: bool = False,
    ):

        self.name = name
        self.var_type = var_type
        self.create_stream = create_stream
        self.is_adc = is_adc

    def declare_var(self):
        self.q_var = qua.declare(self.var_type)

        if self.create_stream:
            self.stream = qua.declare_stream()
        else:
            self.stream = None

    def save(self):
        qua.save(self.q_var, self.stream)

    def process_stream(self, buffer_dim: tuple[int], save_all: bool = True):
        if save_all:
            self.stream.buffer(*buffer_dim).save_all(self.name)
        else:
            self.stream.buffer(*buffer_dim).save(self.name)
