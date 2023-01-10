from fastapi import Cookie, FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, Response
from pydantic import BaseModel
import starlette.status as status
from typing import Optional
import base64
import deta
from deta import Deta
import moviepy.editor as mpy
import sqlite3
import os
import subprocess
import hashlib

# Creating FastAPI Objects
app = FastAPI()
security = HTTPBasic()

# Path to static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja Temlates Directory
templates = Jinja2Templates(directory="templates")

# SessionMiddleware secret key
app.add_middleware(SessionMiddleware, secret_key="eA]a^#vt9%qzRC.")

# Initialize Deta
# Key Description: Project Key: 1c7uiq
deta = Deta("d0tcw6hl_21EUw8bQghxyF8npDrzDRhyJd6jJpvDp")
# Connect to or create a database.
db = deta.Base("LMS")
drive = deta.Drive("LMS")

# Unauthorized Access
unauthorizedAccess = """"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
    <title>Unauthorized Access</title>
</head>
<body>
 <div class="d-flex align-items-center justify-content-center vh-100">
            <div class="text-center">
                <h1 class="display-1 fw-bold py-5">Unauthorized Access Attempt!</h1>
                <p class="lead">
                    You will be returned to Homepage in <span class="seconds">5</span> seconds.
                </p>
                <a href="index.html" class="btn btn-primary">Go Home</a>
            </div>
        </div>

    <script>
        setTimeout(function() {
                window.location.href = "/";
            }, 5000);  // Redirect after 5 seconds
            function startCountdown() {
                var countdown = 5;
                var interval = setInterval(function() {
                countdown--;
            document.querySelector(".seconds").innerHTML = countdown;
            if (countdown === 0) {
                clearInterval(interval);
            document.querySelector(".text-danger").innerHTML = "You have been returned to the homepage.";
            }
            }, 1000);
        }

        startCountdown();

    </script>   
</body>
</html>
    """


# Endpoints / Routes
# Homepage
@app.get("/", response_class=HTMLResponse)
async def homePage(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("index.html", {"request": request, "isLogin": isLogin, "role": role})

# Sign Up page for students and teachers
@app.get("/signup/", response_class=HTMLResponse)
async def signUp(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("sign-up.html", {"request": request, "isLogin": isLogin, "role": role})

@app.post("/signup/")
async def signUpPost(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...), course: Optional[str] = Form(None)):
    # Generate a random salt
    salt = os.urandom(32)
    # Convert salt to base64 string
    encoded_salt = base64.b64encode(salt).decode()
    # Hash the password and salt as bytes
    hashed_password = hashlib.sha256(password.encode() + salt).hexdigest()
    if role == "teacher":
        db.insert({"key": email,"user_details": {"name": name, "email": email,"password": hashed_password, "encoded_salt": encoded_salt, "role": role, "course": course,}})
    else:
        db.insert({"key": email,"user_details": {"name": name, "email": email,"password": hashed_password, "encoded_salt": encoded_salt, "role": role,}})
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)



# Log In Page
@app.get("/login/", response_class=HTMLResponse)
async def login(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("login.html", {"request": request, "isLogin": isLogin, "role": role})

@app.post("/login/", response_class=HTMLResponse)
def loginPost(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    # Check if user with provided email exists in database
    result = db.get(email)
    user = result['user_details']
    
    if user:
        encoded_salt = user['encoded_salt']
        salt = base64.b64decode(encoded_salt)
        # Hash the provided password
        hashed_password = hashlib.sha256(password.encode() + salt).hexdigest()
        # Compare the hashed password to the stored hashed password
        if user['password'] == hashed_password:
            # Set session variables
            request.session["email"] = email
            request.session.setdefault("isLogin", True)
            request.session.setdefault("role", user['role'])
            # Return success response
            return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    else:
        # Return error message
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


# Log Out
@app.get("/logout/", response_class=HTMLResponse)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

# Student logged in account page
@app.get("/my-account/", response_class=HTMLResponse)
async def myAccount(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("/my-account/my-account.html", {"request": request, "isLogin": isLogin, "role": role})

# Teacher Dashboard page
@app.get("/teacher-dashboard/", response_class=HTMLResponse)
async def teacherDashboard(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    if role == "teacher":
        return templates.TemplateResponse("/teacher-dashboard/teacher-dashboard.html", {"request": request, "isLogin": isLogin, "role": role, "template_path": ""})
    else:
        return HTMLResponse(unauthorizedAccess)

@app.get("/teacher-dashboard/{id}", response_class=HTMLResponse)
async def teacherDashboard(request: Request, id:str):
    email = request.session.get('email')
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    # Connecting to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    # Selecting the videos uploaded by the teacher who is accessing the dashboard
    cursor.execute('SELECT * FROM videos WHERE course IN (SELECT course FROM teacher_courses WHERE email = ?)', (email,))
    videos = cursor.fetchall()
    # Commit the transaction
    conn.commit()
    # Close the connection
    conn.close()
    template_path = ""
    if id == "contact-queries":
        query = {"contact_query.email?contains":"@"}
        contact_queries = next(db.fetch(query))
        template_path = "/teacher-dashboard/contact-queries.html"
    elif id == "students-list":
        query = {"user_details.role":"student"}
        students = next(db.fetch(query))
        template_path = "/teacher-dashboard/students-list.html"
    elif id == "videos-list":
        template_path = "/teacher-dashboard/videos-list.html"
    
    # Access To The Teacher's Dashboard
    if role == "teacher":
        return templates.TemplateResponse("/teacher-dashboard/teacher-dashboard.html", {"request": request, "isLogin": isLogin, "role": role, "queries": contact_queries, "videos": videos, "students": students, "template_path": template_path })
    else:
        return HTMLResponse(unauthorizedAccess)

# Page to upload videos to course by teachers
@app.get("/upload-video/", response_class=HTMLResponse)
async def uploadVideo(request: Request):
    isLogin = request.session.get('isLogin')
    role = request.session.get('role')
    message = request.session.get("message")
    if not message:
        message = ""
    if role == "teacher":
        response = templates.TemplateResponse("upload-video.html", {"request": request, "isLogin": isLogin, "role": role, "message": message})
    else:
        response = HTMLResponse(unauthorizedAccess)
    # Delete the message from the session after it has been retrieved
    if "message" in request.session:
        del request.session["message"]
    return response


@app.post("/upload-video/")
async def uploadVideoPost (request: Request, title: str = Form(...), description: str = Form(...), file: UploadFile = File(...)):
    email = request.session.get('email')
    result = db.get(email)
    user = result['user_details']
    user_course = user['course']

    # Use the user's course if the user is a teacher,
    course = user_course

    # Get the base file name and file extension
    base_name, file_extension = os.path.splitext(file.filename)

    # Set the initial file path
    file_path = f"static/uploads/{course}/{new_filename}"

    # Set the thumbnail folder path
    thumbnail_folder = "static/uploads/" + course + "/thumbnail"

    # Set the initial file name
    new_filename = file.filename

    # Set the initial thumbnail image name
    new_thumbnail_name = base_name + "-thumbnail" + file_extension

    # Set the initial counter to 1
    counter = 1

    # Loop until we find a filename that does not exist yet
    while os.path.exists(file_path):
        # Increment the counter
        counter += 1

        # Generate the new filename
        new_filename = base_name + " (" + str(counter) + ")" + file_extension

        # Update the file path
        file_path = "static/uploads/" + course + "/" + new_filename

        # Generate the new thumbnail image name
        new_thumbnail_name = base_name + " (" + str(counter) + ")" + file_extension

        # Update the thumbnail image path
        thumbnail_path = os.path.join(thumbnail_folder, new_thumbnail_name)

    # Save the uploaded file to a buffer
    buffer = file.file.read()

    # Set the file path for Deta's Drive
    file_path = f"static/uploads/{course}/{new_filename}"

    # Save the file to Deta's Drive
    drive.put(file_path, buffer, content_type=file.content_type)

    # Generate the thumbnail image using MoviePy, but save it to a buffer instead of a local file
    thumbnail_buffer = video.save_frame(thumbnail_path, t='00:00:01')

    # Set the thumbnail file path for Deta's Drive
    thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)

    # Save the thumbnail image to Deta's Drive
    drive.put(thumbnail_path, thumbnail_buffer, content_type='image/jpeg')

    # Create the thumbnail folder if it does not exist
    if not os.path.exists(thumbnail_folder):
        os.makedirs(thumbnail_folder)

    # Generate the thumbnail image using MoviePy
    video = mpy.VideoFileClip(file_path)
    thumbnail_filename = os.path.splitext(new_filename)[0] + '.jpg'
    thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)
    thumbnail = video.save_frame(thumbnail_path, t='00:00:01')
    video.close()

    # Execute an INSERT statement to add the file path to the database
    # Open a connection to the database
    try:
        db.insert({"key": title,"video": {"title": title, "description": description,"course": course, "file_path": file_path, "thumbnail_path": thumbnail_path,}})
    except Exception as e:
        # If a unique constraint error occurs, return a redirect response with a message
        request.session["message"] = 'A video with the same title already exists. Make sure that you are uploading the right video. If yes, please change the title.'
        return RedirectResponse("/upload-video/", status_code=status.HTTP_302_FOUND)

    # return {"filename": file.filename, "file_path": file_path}
    return RedirectResponse(f"/{course}/course-videos/", status_code=status.HTTP_302_FOUND)

# Delete uploaded videos by the teacher

@app.post("/delete-video/{title}/{course}")
async def delete_video(request: Request, title: str, course: str):
    if request.method == "POST":
        # Connect to the database
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        # Select the video file path and thumbnail path from the database
        cursor.execute("SELECT file_path, thumbnail_path FROM videos WHERE title = ? AND course = ?", (title, course))
        file_path, thumbnail_path = cursor.fetchone()

        # Delete the video file and thumbnail from the server
        os.remove(file_path)
        os.remove(thumbnail_path)

        # Delete the video from the videos table
        cursor.execute("DELETE FROM videos WHERE title = ? AND course = ?", (title, course))
        # Delete the comments on the video from comments table
        cursor.execute("DELETE FROM comments WHERE file_path = ?", (file_path,))

        # Commit the transaction
        conn.commit()

        # Close the connection
        conn.close()

        # Redirect back to the teacher dashboard page
        return RedirectResponse("/teacher-dashboard/videos-list", status_code=status.HTTP_302_FOUND)







# All courses list
@app.get("/all-courses/", response_class=HTMLResponse)
async def allCourses(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("courses.html", {"request": request, "isLogin": isLogin, "role": role})

# Course playlist 
@app.get("/{course_name}/course-videos/")
def courseVideos(course_name: str, request: Request):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    # Fetch the video records for the specified course
    cursor.execute("SELECT * FROM videos WHERE course=?", (course_name,))
    videos = cursor.fetchall()
    conn.close()
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("course-videos.html", {"request": request, "videos": videos, "isLogin": isLogin, "role": role })

# Videos
@app.get("/{course_name}/course-videos/{path:path}")
def show_video(course_name: str, path: str, request: Request):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    # Fetch the video records for the specified course
    cursor.execute("SELECT * FROM videos WHERE course=?", (course_name,))
    videos = cursor.fetchall()
    cursor.execute("""
        SELECT c.file_path, c.comment, u.name
        FROM comments AS c
        INNER JOIN users AS u ON c.email = u.email
        WHERE c.file_path=?
    """, (path,))
    comments = cursor.fetchall()
    conn.close()
    email = request.session.get('email')
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    # Find the video with the matching file path
    for video in videos:
        if video[3] == path:
            video_title = video[0]
            video_description = video[1]
            video_course = video[2]
            break
    if role == "teacher" or role == "student":
    # code to execute if role is either "teacher" or "student"
        return templates.TemplateResponse("playlist.html", {"request": request, "email": email, "path": path, "video_course": video_course, "videos": videos, "video_description": video_description, "video_title":video_title, "isLogin": isLogin, "role": role, "comments": comments })
    else:
    # code to execute if role is neither "teacher" nor "student"
        return HTMLResponse(unauthorizedAccess)

# Comments
@app.post("/comments/")
def save_comment(path: str = Form(...), course: str = Form(...), email: str = Form(...), comment: str = Form(...)):
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    # Insert the new comment into the database
    cursor.execute("INSERT INTO comments (file_path, comment, email) VALUES (?, ?, ?)", (path, comment, email))
    # Commit the transaction
    conn.commit()
    # Close the connection
    conn.close()
    # Redirect the user back to the video page
    return RedirectResponse(f"/{course}/course-videos/{path}", status_code=status.HTTP_302_FOUND)


# About the LMS 
@app.get("/about/", response_class=HTMLResponse)
async def about(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("about.html", {"request": request, "isLogin": isLogin, "role": role})


# Contact Page
@app.get("/contact/", response_class=HTMLResponse)
async def contactUs(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("contact.html", {"request": request, "isLogin": isLogin, "role": role})

@app.post("/contact/")
async def contactUsPost(request: Request, name: str = Form(...), email: str = Form(...), phone: str = Form(...), query: str = Form(...)):
    db.insert({"contact_query": {"name": name, "email": email, "phone": phone, "query": query}})
    return RedirectResponse("/contact/", status_code=status.HTTP_302_FOUND, headers={"msg": "Form submitted successfully"})

# Discussion Forum
# Create/Post topics
@app.get("/create-topic/", response_class=HTMLResponse)
async def createTopic(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("/discussion-forum/create-topic.html", {"request": request, "isLogin": isLogin, "role": role})

@app.post("/topics/create")
def createTopicPost(request: Request, title: str = Form(...), description: str = Form(...)):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Get the email of the user who created the topic from the session
    created_by = request.session.get("email")

    # Get the name of the user who created the topic
    cursor.execute("SELECT name FROM users WHERE email = ?", (created_by,))
    created_by_name = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO topics (title, description, created_by, created_by_name)
        VALUES (?, ?, ?, ?)
        """,
        (title, description, created_by, created_by_name),
    )

    conn.commit()

    # return {
    #     "id": cursor.lastrowid,
    #     "title": title,
    #     "description": description,
    #     "created_by": created_by,
    #     "created_by_name": created_by_name,
    # }

# List all the existing topics
@app.get("/topics/")
def list_topics(request: Request):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT topics.*, users.name AS created_by_name
        FROM topics
        JOIN users ON topics.created_by = users.email
        """
    )
    topics = cursor.fetchall()

    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("/discussion-forum/list-topics.html", {"request": request, "isLogin": isLogin, "role": role, "topics": topics })

# Opens topic and lists all the replies to it
@app.get("/topics/{topic_id}")
def view_topic(request: Request, topic_id: int):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT topics.*, users.name AS created_by_name
        FROM topics
        JOIN users ON topics.created_by = users.email
        WHERE topics.id = ?
        """,
        (topic_id,),
    )
    topic = cursor.fetchone()

    cursor.execute(
        """
        SELECT replies.*, users.name AS created_by_name
        FROM replies
        JOIN users ON replies.created_by = users.email
        WHERE replies.topic_id = ?
        """,
        (topic_id,),
    )
    replies = cursor.fetchall()

    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("/discussion-forum/topic.html", {"request": request, "isLogin": isLogin, "role": role, "topic": topic, "replies": replies})

# Reply to the topics

@app.post("/replies/create")
def create_reply(request:Request, topic_id: int =Form(...) , reply: str =Form(...)):
    email = request.session.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name FROM users WHERE email = ?
        """,
        (email,),
    )

    name = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO replies (topic_id, reply, created_at, created_by, created_by_name)
        VALUES (?, ?, datetime('now'), ?, ?)
        """,
        (topic_id, reply, email, name),
    )

    conn.commit()

    return RedirectResponse(f"/topics/{topic_id}", status_code=status.HTTP_302_FOUND)