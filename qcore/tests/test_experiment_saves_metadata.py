from datetime import date
from pathlib import Path

from qcore.helpers.datasaver import Datasaver


def test_save_dict_as_metadata():
    today = date.today()
    path = Path(f'./test_{today}.h5')
    ds = Datasaver(path)

    with ds:
        ds.save_metadata({
            "settings": {
                "RF_inputs": {
                    1: {
                        "gain": 0
                    }
                },
                "RF_outputs": {
                    1: {
                        "gain": 0
                    }
                }
            }
        })


if __name__ == '__main__':
    test_save_dict_as_metadata()
