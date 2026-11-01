from flask import Flask, render_template, request, send_from_directory, abort
from google import genai
import csv
import os

app = Flask(__name__)
client = genai.Client(api_key="1234")
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
DOWNLOAD_DIRECTORY = os.path.join(app.root_path, "downloads")
ALLOWED_EXTENSIONS = {'PDF', 'DOC', 'DOCX', 'TXT', 'RTF', 'HWP', 'HTML','XLS',
                      'XLSX', 'CSV', 'TSV','PPT','PPTX', 'PNG', 'JPEG',
                      'JPG', 'WEBP', 'GIF', 'SVG',}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
model="gemini-3.1-flash-lite"
debug_mode = True

def debug_print(text):
    if debug_mode == True:
        print(text)


def query_ai(question_num,topic,is_file_uploaded,filename):
    ai_prompt = f'you are making a gimkit where each question has 4, multiple choice, responses and only 1 answer is correct. Generate exactly {question_num} questions about {topic}. Only answer in the strict format of ("Title"correct_awnser,wrong_1,wrong_2,wrong_3) wrapping each the {question_num} questions around parentheses and separating the questions using ;Make sure to make Exactly {question_num} questions so that you have {question_num} sets of parentheses and {question_num} sets of answers, do not use commas in any of the actual anwsers to the questions, if you must use them put the ^ symbol instead.'
    if is_file_uploaded: #only uploads file when it exists 
        uploaded_file = client.files.upload(file=f"uploads/{filename}")
        response = client.models.generate_content(contents=[uploaded_file,ai_prompt],model=model) #Use generate_content for both of theese so that ai dose not maintain memory over sessions
    else:
        response = client.models.generate_content(contents=ai_prompt,model=model)

    response = str(response.text)
    response = response.replace("(","") #removes left parenthesis from the string
    response_list = response.split(")") #turns the string of questions into a list 
    response_list = response_list[:question_num] #cuts off any extra text that the ai might have put
    return response_list

def ai_to_list(response):
    indices = []
    for index, char in enumerate(response): #gets the location of all quotation marks in string. 
        if char == '"':
            indices.append(index)
    second_quote = indices[-1]
    question_title = response[1:second_quote]
    answers = response[second_quote+1:]
    answers = answers.split(",")

    response_formatted = [question_title,answers[0],answers[1],answers[2],answers[3]]
    return response_formatted

def append_list(my_list): #will append the extra lines of questions to the empty gimkit format 
    with open("downloads/template.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(my_list)

def reset_csv():
    template = """Gimkit Spreadsheet Import Template,,,, 
    Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2 (Optional),Incorrect Answer 3 (Optional)
    """
    with open("downloads/template.csv", "w", encoding="utf-8") as file:
        file.write(template)

@app.route('/' )
def hello_world():# put application's code here
    reset_csv()
    return render_template('index.html')

@app.route('/generate',methods = ["POST","GET"])
def generate_gimkit():
    question_num = request.form.get('question_num')
    topic = request.form.get('topic')
    debug_print(request.files)
    file = request.files['file']
    debug_print("request.files success")
    filename = file.filename

    if filename != '':
        debug_print("File input sucsess")
        file_ext = os.path.splitext(filename)[1][1:].upper()
        if file_ext not in ALLOWED_EXTENSIONS:
            debug_print(f"Invalid Extenion: {file_ext}")
            abort(400)
        else:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ai_response = query_ai(int(question_num),topic,True,filename)

    else:
        ai_response = query_ai(int(question_num),topic,False,"")
    for i in range(len(ai_response)):
        try: #catches any inconsitensies in ai response
            append_list(ai_to_list(ai_response[i]))
        except:
            debug_print("append failed")

    return send_from_directory(
        DOWNLOAD_DIRECTORY,
        'template.csv',
        as_attachment=True
    )


if __name__ == '__main__':
    app.run()
