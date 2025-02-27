import faiss

class VectorStore:
    def __init__(self):
        self.index = faiss.IndexFlatL2(128)

    def add(self, vectors):
        self.index.add(vectors)

    def search(self, vector, k=5):
        return self.index.search(vector, k)