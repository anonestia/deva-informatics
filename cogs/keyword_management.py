from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .chat_manager import generate_agent_response
from rapidfuzz import fuzz

def preprocess_keywords(entry_keywords):
    """
    Generate variations of keywords for typo tolerance and abbreviation matching.
    """
    keywords = entry_keywords.split(", ")
    variations = set()
    
    for kw in keywords:
        words = kw.split()
        variations.add(kw.lower())  # Original lowercase
        variations.add("".join(word[0] for word in words))  # Abbreviation (first letters)
    
    return " ".join(variations)

def detect_intent(chat_history):
    """
    Determine if the chat is requesting general or detailed information.
    """
    
    prompt= (
        f"There is a conversation below:\n{chat_history}"
        "You are replying as Deva. She needs to recall information. Are the information needed must be detailed, or general?"
        "General information is needed when only shallow information required, usually simple questions that answers What, Who, When, and Where. Detailed information demands for calculation, answers Why and How, in depth, and other _details._"
        "If the information needed is only general, write General. Otherwise, return Detailed. Write without additional words, nor period."
    )
    
    result = generate_agent_response(prompt).strip()
    
    print(f"Keyword intent detection: {result}")
    
    if result == "General" or result == "Detailed":
        return result
    else:
        return "General"
    
    ### Non-AI decision
    # detailed_keywords = ["calculation", "how to", "best way", "mechanics", "explain", "formula", "optimal", "strategy", "cara", "hitung", "rumus", "kalkulasi", "hitungan", "matematika", "jelaskan", "jelasin"]
    # general_keywords = ["what is", "what are", "list of", "overview", "basics", "types of", "examples of", "apa", "daftar", "basic"]

    # chat_lower = chat_history.lower()
    
    # if any(word in chat_lower for word in detailed_keywords):
    #     return "Detailed"
    # if any(word in chat_lower for word in general_keywords):
    #     return "General"
    
    # return "General"  # Default to General if unclear

def get_entries(entries, id_indices, intent):
    """
    Retrieves the corresponding entries with the correct category (General/Detailed).
    Returns a list of formatted string outputs.
    """
    retrieved_data = []
    for entry_id in id_indices:
        for entry in entries:
            if entry[0] == entry_id:
                category = 2 if intent == "Detailed" and "Detailed" in entry else 1
                retrieved_data.append(category)
                break

    # Ensure it always returns a list
    return retrieved_data if retrieved_data else []

def find_similar_entries(entries, chat_history, top_n=5, threshold=0.15):
    """
    Find the most relevant keyword entries based on the chat history.
    Returns a list of entry IDs.
    """
    intent = detect_intent(chat_history)
    
    entry_dict = {entry[0]: {"title": entry[1], "keywords": entry[2], "categories": entry[3:]} for entry in entries}

    documents = []
    entry_map = []
    
    for entry_id, data in entry_dict.items():
        processed_keywords = preprocess_keywords(data["keywords"])
        documents.append(f"{data['title']} {data['keywords']} {processed_keywords}")
        entry_map.append(entry_id)
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents + [chat_history])
    
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    
    auto_picked = set()
    for i, entry_id in enumerate(entry_map):
        title = entry_dict[entry_id]["title"].lower()
        if fuzz.partial_ratio(title, chat_history.lower()) >= 80:
            auto_picked.add(entry_id)
    
    valid_entries = [(entry_map[i], similarity_scores[i]) for i in range(len(similarity_scores)) if similarity_scores[i] >= threshold]
    valid_entries.sort(key=lambda x: x[1], reverse=True)
    
    top_results = [entry_id for entry_id, _ in valid_entries[:top_n]]
    
    final_results = set(top_results) | auto_picked
    
    return list(final_results), intent