from fastapi import Cookie, FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, Response
import starlette.status as status
from typing import Optional
import moviepy.editor as mpy
import sqlite3
import os
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

# Database Path
db ="lms.db"

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
    # Hash the password and salt as bytes
    hashed_password = hashlib.sha256(password.encode() + salt).hexdigest()
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    if role == "teacher":
        # Insert the user into the users table
        cursor.execute("INSERT INTO users (name, email, password, salt, role) VALUES (?, ?, ?, ?, ?)", (name, email, hashed_password, salt, role))
        # Insert the course into the teacher_courses table
        cursor.execute("INSERT INTO teacher_courses (email, course) VALUES (?, ?)", (email, course))
    else:
        # Insert the user into the users table
        cursor.execute("INSERT INTO users (name, email, password, salt, role) VALUES (?, ?, ?, ?, ?)", (name, email, hashed_password, salt, role))
    # Commit the transaction
    conn.commit()
    # Close the connection
    conn.close()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


# Log In Page
@app.get("/login/", response_class=HTMLResponse)
async def login(request: Request):
    isLogin = request.session.get('isLogin')
    role= request.session.get('role')
    return templates.TemplateResponse("login.html", {"request": request, "isLogin": isLogin, "role": role})

@app.post("/login/", response_class=HTMLResponse)
def loginPost(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Retrieve the salt and hashed password for the user
    cursor.execute('SELECT salt, password FROM users WHERE email=?', (email,))
    result = cursor.fetchone()
    if result:
        salt = result[0]
        stored_password = result[1]
    else:
        # No user with the given email was found
        return templates.TemplateResponse("/login.html", {"request": request, "msg": "Invalid Username or Password"})

    # Hash the password the user entered with the retrieved salt
    entered_password = hashlib.sha256(password.encode() + salt).hexdigest()

    # Compare the stored password to the entered password
    if entered_password == stored_password:
        # Password is correct, retrieve the user's role
        cursor.execute('SELECT role FROM users WHERE email=?', (email,))
        role = cursor.fetchone()[0]
        # Set session variables
        request.session["email"] = email
        request.session.setdefault("isLogin", True)
        request.session.setdefault("role", role)
        # Redirect to the home page
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    else:
        # Password is incorrect
        return templates.TemplateResponse("/login.html", {"request": request, "msg": "Invalid Username or Password"})

def hash_password(password, salt):
    # Append the salt to the password
    salted_password = password + salt
    # Hash the salted password
    hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
    return hashed_password


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
    # Accessing Contact Queries
    cursor.execute('SELECT * FROM contact_queries')
    queries = cursor.fetchall()
    # Accessing Student List
    cursor.execute('SELECT * FROM users WHERE role="student"')
    students = cursor.fetchall()
    # Selecting the videos uploaded by the teacher who is accessing the dashboard
    cursor.execute('SELECT * FROM videos WHERE course IN (SELECT course FROM teacher_courses WHERE email = ?)', (email,))
    videos = cursor.fetchall()
    # Commit the transaction
    conn.commit()
    # Close the connection
    conn.close()
    template_path = ""
    if id == "contact-queries":
        template_path = "/teacher-dashboard/contact-queries.html"
    elif id == "students-list":
        template_path = "/teacher-dashboard/students-list.html"
    elif id == "videos-list":
        template_path = "/teacher-dashboard/videos-list.html"
    
    # Access To The Teacher's Dashboard
    if role == "teacher":
        return templates.TemplateResponse("/teacher-dashboard/teacher-dashboard.html", {"request": request, "isLogin": isLogin, "role": role, "queries": queries, "videos": videos, "students": students, "template_path": template_path })
    else:
        return HTMLResponse(unauthorizedAccess)

# Page to upload videos to course by teachers
@app.get("/upload-video/", response_class=HTMLResponse)
async def uploadVideo(request: Request):
    isLogin = request.session.get('isLogin')
    role = request.session.get('role')
    if role == "teacher":
        return templates.TemplateResponse("upload-video.html", {"request": request, "isLogin": isLogin, "role": role})
    else:
        return HTMLResponse(unauthorizedAccess)

@app.post("/upload-video/")
async def uploadVideoPost (request: Request, title: str = Form(...), description: str = Form(...), file: UploadFile = File(...), email: str = Form(...)):
    
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    # Fetch the user's role and course from the database
    cursor.execute("SELECT role, course FROM users LEFT JOIN teacher_courses ON users.email = teacher_courses.email WHERE users.email = ?", (email,))
    user = cursor.fetchone()
    # Close the connection
    conn.close()

    # Use the user's course if the user is a teacher,
    # otherwise use the course provided in the form
    if user[0] == "teacher":
        course = user[1]
    else:
        course = course

    # (file: UploadFile, folder: str):
    # Create the specified folder if it does not exist
    if not os.path.exists("static/uploads/" + course):
        os.makedirs("static/uploads/" + course)

    # Save the uploaded file to the specified folder
    file_path = "static/uploads/" + course + "/" + file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    # Generating Thumbnail And Storing its path to the database
    thumbnail_folder = os.path.join(os.path.dirname(file_path), 'thumbnail')
    if not os.path.exists(thumbnail_folder):
        os.makedirs(thumbnail_folder)

    # Generating Thumbnail And Storing its path to the database
    video = mpy.VideoFileClip(file_path)
    thumbnail_filename = os.path.splitext(file.filename)[0] + '.jpg'
    thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)
    thumbnail = video.save_frame(thumbnail_path, t='00:00:01')

    # Execute an INSERT statement to add the file path to the database
    # Open a connection to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (title, description, course, file_path, thumbnail_path) VALUES (?, ?, ?, ?, ?)", (title, description, course, file_path, thumbnail_path))
    
    # Commit the transaction
    conn.commit()

    # Close the connection
    conn.close()
    # return {"filename": file.filename, "file_path": file_path}
    return RedirectResponse(f"/{course}/course-videos/", status_code=status.HTTP_302_FOUND)

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
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    # Insert the data into the contact_queries table
    cursor.execute("INSERT INTO contact_queries (name, email, phone, query) VALUES (?, ?, ?, ?)", (name, email, phone, query))
    
    # Commit the transaction
    conn.commit()
    
    # Close the connection
    conn.close()
    
    # Redirect back to the /contact/ page with a success message
    return RedirectResponse("/contact/", status_code=status.HTTP_302_FOUND, headers={"msg": "Form submitted successfully"})