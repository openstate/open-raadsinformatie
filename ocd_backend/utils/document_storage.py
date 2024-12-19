from ocd_backend.settings import DATA_DIR_PATH


class DocumentStorage():
    @classmethod
    def _id_partitioned(cls, id):
        thousands = id//1000
        thousands_as_string = str(thousands).zfill(9)
        return f"{thousands_as_string[0:3]}/{thousands_as_string[3:6]}/{thousands_as_string[6:]}"
    
    @classmethod
    def full_name(cls, id, name):
        return f"{DATA_DIR_PATH}/{cls._id_partitioned(id)}/{name}"
