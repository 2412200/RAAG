from fastapi import APIRouter
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

router = APIRouter()

categories = [
    "Womens Wear",
    "Mens Wear",
    "Home Appliances",
    "Beauty",
    "Books",
    "Groceries"
]
@router.get("/search")
def search(categories):

    vectorizer = TfidfVectorizer()
    category_vectors = vectorizer.fit_transform(categories)

    query = input("Enter the category: ")

    query_vector = vectorizer.transform([query])

    similarity = cosine_similarity(query_vector, category_vectors)

    scores = similarity[0]

    results = []

    for i, score in enumerate(scores):
        if score > 0:
            results.append(categories[i])

    return results

if __name__ == "__main__":

    result = search(categories)
    print(result)