# LMS
This is a Learning Management System (LMS) built using FastAPI, Jinja2, moviepy, python-multipart, uvicorn, itsdangerous, Starlette, and sqlite3.

##Endpoints
### Homepage
GET /

Displays the homepage of the LMS.

### Signup
GET /signup/

Displays the signup form for new users.  The user can choose to be either a teacher or a student. If the user selects the role of a teacher, options for courses will be displayed. The implementation of this functionality utilizes JavaScript
```JavaScript
  <script>
  document.addEventListener("DOMContentLoaded", () => {
  const roleSelect = document.getElementById("role");
  const courseSelect = document.getElementById("course");

  roleSelect.addEventListener("change", () => {
    if (roleSelect.value === "teacher") {
      courseSelect.style.display = "block";
    } else {
      courseSelect.style.display = "none";
    }
  });
});
</script>
```

### POST /signup/

This endpoint handles the submission of the signup form and creates a new user account.

### Login
GET /login/

Displays the login form.

### POST /login/

Submits the login form and logs the user in.

### Logout
GET /logout/

Logs the user out.

### My Account
GET /my-account/

Displays the user's account page.

## Teacher Dashboard
GET /teacher-dashboard/

Displays the teacher dashboard page.

GET /teacher-dashboard/{id}

Displays the teacher dashboard page for a specific path. There are two paths included.
```python
  template_path = ""
    if id == "contact-queries":
        template_path = "/teacher-dashboard/contact-queries.html"
    elif id == "student-list":
        template_path = "/teacher-dashboard/student-list.html"
```

### Upload Video
GET /upload-video/

Displays the form for uploading a new video.

POST /upload-video/

Submits the form and uploads a new video, generates a thumbnail, links it to the video in the database.

### All Courses
GET /all-courses/

Displays a list of all available courses.

### Course Videos
GET /{course_name}/course-videos/

Displays a list of videos for a specific course.

GET /{course_name}/course-videos/{path}

Displays a specific video for a course.

### Comments
POST /comments/

Saves a comment for a specific video in the database.

### About
GET /about/

Displays the about page.

### Contact Us
GET /contact/

Displays the contact us form.

POST /contact/

Submits the contact us form.