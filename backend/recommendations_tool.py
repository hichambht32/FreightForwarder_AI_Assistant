import pymysql
import Levenshtein

def getSimilarNames(input: str):
    threshold: int = 20
    response= []
    similar_names = []
    try:
        conn = pymysql.connect(
            host='192.168.2.134',
            user='aiuser',
            password='topnegoce',
            db='adildb',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cur = conn.cursor()
        cur.execute("SELECT name,code,chapter_title,category FROM codification WHERE name IS NOT NULL;")
        results = cur.fetchall()
        cur.close()
        conn.close()

        for result in results:
            distance = Levenshtein.distance(input, result['name'])
            if distance <= threshold:
                similar_names.append((result['name'], distance,result['code'],result['chapter_title'],result['category']))
        similar_names_sorted = sorted(similar_names, key=lambda x: x[1])
        top_5_similar_names = similar_names_sorted[:5]
        #formatting the response
        for i,(name, distance,code,chapter_title,category) in enumerate(top_5_similar_names, start=1):
            ordinal = f"{i}{'st' if i == 1 else 'nd' if i == 2 else 'rd' if i == 3 else 'th'}"
            response.append((f"{ordinal} in similarity: Name: {name} with the highest similarity of {distance}", 
                     f"Levenshtein Distance: {distance}",  
                     f"code: {code}", 
                     f"chapter_title: {chapter_title}", 
                     f"category: {category}"))
            # response.append((f"Name: {name} with the highest similarity of {distance} ", f"Levenshtein Distance: {distance}",  f"code:{code}", f"chapter_title:{chapter_title}", f"category:{category}"))

        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__=="__main__":
    similar_names = getSimilarNames('acide citrique')
    for name, distance,code,chapter_title,category in similar_names:
        print(f"Name: {name}, Levenshtein Distance: {distance},  code:{code}, chapter_title:{chapter_title},  category:{category}")

