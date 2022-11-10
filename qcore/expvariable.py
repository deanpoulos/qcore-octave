from qm import qua

class ExpVar:

    def __init__(
                self,
                name: str,
                var_type: type,
                create_stream: bool = True,
                is_adc: bool = False
            ):

        self.name = name
        self.var_type = var_type
        self.q_var = qua.declare(var_type)

        if create_stream:
            self.stream = qua.declare_stream(is_adc=is_adc)
        else:
            self.stream = None
    
    def save(self):
        qua.save(self.q_var, self.stream)

    def process_stream(self, save_all: bool = True):

        if save_all:
            self.stream.save_all(self.name)
        else:
            self.stream.save(self.name)
