# To generate input data:
#   - Note: this requires invoking docker without a password. On the servers
#       - sudo visudo
#       - add a line "rob ALL=(root) NOPASSWD: /usr/bin/docker" 
#   - ssh canis 'sudo docker exec -t ori_elastic_1 curl "localhost:9200/_cat/indices?bytes=mb&s=index"' > cat_indices_canis.txt
#   - ssh wolf 'sudo docker exec -t ori_elastic_1 curl "localhost:9200/_cat/indices?bytes=mb&s=index"' > cat_indices_wolf.txt

class CatIndicesCompare:
    def compare(self):
        indices_canis = self.read_cat_indices("cat_indices_canis.txt")
        indices_wolf = self.read_cat_indices("cat_indices_wolf.txt")

        self.output_indices(indices_canis, indices_wolf)

        self.output_differences(indices_canis, indices_wolf)

    def read_cat_indices(self, file_name):
        with open(file_name, 'r') as f:
            index_lines = f.readlines()
        
        indices = {}
        for index_line in index_lines:
            columns = index_line.split()
            index_name = columns[2].replace("_fixed_", "_")            
            index_size1 = int(columns[8])
            index_size2 = int(columns[9])
            if index_size1 != index_size2:
                raise Exception(f"Sizes of last 2 columns should be equal: {index_size1} {index_size2}")

            name = '_'.join(index_name.split("_")[0:-1])
            if indices.get(name) is not None:
                raise Exception(f"Duplicate index found for {name} in {file_name}")
            indices[name] = index_size1

        return indices

    def output_indices(self, indices_canis, indices_wolf):
        print("\nSizes of new and old indexes compared")
        n = 0
        for index_name, canis_size in sorted(indices_canis.items(), key=lambda item: item[1], reverse=True):
            if indices_wolf.get(index_name) is None:
                continue
            ratio = 1.0 if indices_wolf[index_name] == 0 else canis_size / indices_wolf[index_name]
            extra = '*' if ratio < 1.0 else ''
            str = f"{index_name:50} {canis_size:6} {indices_wolf[index_name]:6}  {ratio:6.2f}{extra}"
            print(str)
            n = n + 1
        print(f"Total: {n} sources")        

    def output_differences(self, indices_canis, indices_wolf):
        print("\nSources present in new index but not in old:")
        n = 0
        for canis_index_name in indices_canis.keys():
            if indices_wolf.get(canis_index_name) is None:
                print(f"   {canis_index_name}")
                n = n + 1
        print(f"Total: {n} sources")        

        print("\nSources present in old index but not in new:")
        n = 0
        for wolf_index_name in indices_wolf.keys():
            if indices_canis.get(wolf_index_name) is None:
                print(f"   {wolf_index_name}")
                n = n + 1
        print(f"Total: {n} sources")        


CatIndicesCompare().compare()