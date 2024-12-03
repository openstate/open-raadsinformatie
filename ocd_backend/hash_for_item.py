class HashForItem:
    def __init__(self, hash_key, hash_value, provider, site_name, item_type, item_id):
        self.hash_key = hash_key
        self.hash_value = hash_value
        self.provider = provider
        self.site_name = site_name
        self.item_type = item_type
        self.item_id = item_id

    def __repr__(self):
        return f"HashForItem('{self.hash_key}', '{self.hash_value}', '{self.provider}', '{self.site_name}', '{self.item_type}', '{self.item_id}')"