class PdfNaming:
    FORMAT_ORIGINAL = 'original'
    FORMAT_MARKDOWN = 'markdown'
    FORMAT_METADATA = 'metadata'

    @classmethod
    def _id_partitioned(cls, id):
        thousands = id//1000
        thousands_as_string = str(thousands).zfill(9)
        return f"{thousands_as_string[0:3]}/{thousands_as_string[3:6]}/{thousands_as_string[6:]}"
    

    @classmethod
    def _base_name_cls(cls, data_dir_path, id_partitioned, resource_ori_id):
        return f"{data_dir_path}/{id_partitioned}/{resource_ori_id}"


    @classmethod
    def original_name_cls(cls, data_dir_path, stored_document_id, resource_ori_id):
        id_partitioned = cls._id_partitioned(stored_document_id)
        base_name = cls._base_name_cls(data_dir_path, id_partitioned, resource_ori_id)
        return base_name

    @classmethod
    def full_markdown_name_cls(cls, data_dir_path, stored_document_id, resource_ori_id):
        id_partitioned = cls._id_partitioned(stored_document_id)
        base_name = cls._base_name_cls(data_dir_path, id_partitioned, resource_ori_id)
        return f"{base_name}.md"

    @classmethod
    def full_metadata_name_cls(cls, data_dir_path, stored_document_id, resource_ori_id):
        id_partitioned = cls._id_partitioned(stored_document_id)
        base_name = cls._base_name_cls(data_dir_path, id_partitioned, resource_ori_id)
        return f"{base_name}.metadata"
