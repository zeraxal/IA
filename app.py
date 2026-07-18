from flask import Flask, render_template, request, send_from_directory, abort
from google import genai
import csv
import os

app = Flask(__name__)
client = genai.Client(api_key="AIzaSyBu4UVJmNNxg8HS5OrJIIEKshEYX53B5RE")
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
DOWNLOAD_DIRECTORY = os.path.join(app.root_path, "downloads")
ALLOWED_EXTENSIONS = {'PDF', 'DOC', 'DOCX', 'TXT', 'RTF', 'HWP', 'HTML','XLS',
                      'XLSX', 'CSV', 'TSV','PPT','PPTX', 'PNG', 'JPEG',
                      'JPG', 'WEBP', 'GIF', 'SVG',}
app.config["UPLOAD_FOLDER"  ] = UPLOAD_FOLDER

def query_ai(question_num,topic,is_file_uploaded,filename):
    ai_prompt = f'you are making a gimkit where each question has 4, multiple choice, responses and only 1 answer is correct. Generate exactly {question_num} questions about {topic}. Only answer in the strict format of ("Title"correct_awnser,wrong_1,wrong_2,wrong_3) wrapping each the {question_num} questions around parentheses and separating the questions using ;Make sure to make Exactly {question_num} questions so that you have {question_num} sets of parentheses and {question_num} sets of answers, do not use commas in any of the actual anwsers to the questions, if you must use them put the ^ symbol instead.'

    if is_file_uploaded:
        uploaded_file = client.files.upload(file=f"uploads/{filename}")
        response = client.models.generate_content(
            contents=[
                uploaded_file,
                ai_prompt
            ]
        )
    else:
        chat = client.chats.create(model="gemini-3.1-flash-lite")
        response = chat.send_message(ai_prompt)
        response = str(response.text)
    response = response.replace("(","")
    response_list = response.split(")")
    response_list = response_list[:question_num]
    return response_list

def ai_to_list(response):
    indices = [index for index, char in enumerate(response) if char == '"']
    second_quote= indices[-1]
    question_title = response[1:second_quote]
    answers = response[second_quote+1:]
    answers = answers.split(",")

    response_formatted = [question_title,answers[0],answers[1],answers[2],answers[3]]
    return response_formatted

def append_list(my_list):
    with open("downloads/template.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(my_list)

def reset_csv():
    template = """Gimkit Spreadsheet Import Template,,,, 
    Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2 (Optional),Incorrect Answer 3 (Optional)
    """
    with open("downloads/template.csv", "w", encoding="utf-8") as file:
        file.write(template)


app = Flask(__name__)


@app.route('/' )
def hello_world():# put application's code here
    reset_csv()
    return render_template('index.html')

@app.route('/generate',methods = ["POST","GET"])
def generate_gimkit():
    question_num = request.form.get('question_num')
    topic = request.form.get('topic')
    print(request.files)
    file = request.files['file']
    print("if this dosent print it failder here ")
    filename = file.filename
    if filename != '':
        print("we are doing stuff with the fille AHHHHHHHHHHHH")
        file_ext = os.path.splitext(filename)[1][1:].upper()
        if file_ext not in ALLOWED_EXTENSIONS:
            print(f"uh oh your extension was: {file_ext}")
            abort(400)
        else:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ai_response = query_ai(int(question_num),topic,True,filename)
    else:
        ai_response = query_ai(int(question_num),topic,False,"")
    for i in range(len(ai_response)):
        try:
            append_list(ai_to_list(ai_response[i]))
        except:
            continue
    return send_from_directory(
        DOWNLOAD_DIRECTORY,
        'template.csv',
        as_attachment=True
    )


if __name__ == '__main__':
    app.run()
