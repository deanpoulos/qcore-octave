from qm import qua


class Variable:
    def __init__(
        self,
        name: str,
        var_type: type = None,
        create_stream: bool = False,
        is_adc: bool = False,
        save_all: bool = False,
        buffer_dim: tuple[int] = None,
    ):

        self.name = name
        self.var_type = var_type
        self.create_stream = create_stream
        self.is_adc = is_adc
        self.save_all = save_all
        self.buffer_dim = buffer_dim

    def declare_var(self):
        if self.var_type:
            self.q_var = qua.declare(self.var_type)
            if self.create_stream:
                self.stream = qua.declare_stream(is_adc=self.is_adc)
            else:
                self.stream = None
        else:
            pass

    def save(self):
        qua.save(self.q_var, self.stream)

    def process_stream(self):
        if self.stream:
            if self.save_all:
                self.stream.buffer(self.buffer_dim).save_all(self.name)
            else:
                self.stream.buffer(self.buffer_dim).save(self.name)
        else:
            pass
