from ocd_backend.settings import DATA_DIR_PATH


class DocumentStorage():
    @classmethod
    def _id_partitioned(cls, id):
        id_as_string = str(id).zfill(9)
        return f"{id_as_string[0:3]}/{id_as_string[3:6]}/{id_as_string[6:]}"
    
    @classmethod
    def full_name(cls, id, name):
        return f"{DATA_DIR_PATH}/{cls._id_partitioned(id)}/{name}"
