import PyPDF2
import re
import json

def extract_recommendations(pdf_file):
    recommendations = {}
    
    with open(pdf_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            # Search for the section containing the recommendations
            match = re.search(r'Appendix: Recommendation Summary.*?3 Data Plane', text, re.DOTALL)
            if match:
                recommendations_text = match.group(0)
                # Extract each recommendation
                matches = re.findall(r'(\d+\.\d+\.\d+)\s+(.*?)\s+(?:\(Automated\)|\(Manual\))\s+(?:|)', recommendations_text)
                for match in matches:
                    recommendation_id, description = match
                    recommendations[recommendation_id] = {
                        "description": description
                    }
    return recommendations

def save_to_json(recommendations, output_file):
    with open(output_file, 'w') as file:
        json.dump(recommendations, file, indent=4)

if __name__ == "__main__":
    pdf_file = "cis/CIS_Cisco_IOS_15_Benchmark_v4.1.1.pdf"
    output_file = "recommendations.json"

    recommendations = extract_recommendations(pdf_file)
    save_to_json(recommendations, output_file)
