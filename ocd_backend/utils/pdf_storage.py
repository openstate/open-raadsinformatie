
class PdfStorage():

    @classmethod
    def id_partitioned(cls, id):
        id_as_string = str(id).zfill(9)
        return f"{id_as_string[0:3]}/{id_as_string[3:6]}/{id_as_string[6:]}"