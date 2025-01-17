from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms05 import (RegistrationForm, LoginForm, UpdateAccountForm, 
                                PostForm, RequestResetForm, ResetPasswordForm)
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import os, secrets
from PIL import Image

# forms.py in flaskblog package
# models.py in flaskblog package

# http://localhost:5000/
@app.route("/")
@app.route("/home")
def home():
    # get page number from url, default is first page (1),
    # the type (int) is used to make sure page is integer.
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('home13_paginate.html', posts=posts)

# http://localhost:5000/about
@app.route("/about")
def about():
    return render_template('about11_flash.html', title='About')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    # once submit successfully, flash message shows in the placehold in layout.html
    # flash message is one time only, it disappear after refresh web browser
    if form.validate_on_submit():
        # hash the password
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pwd)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        # 'home' is function of home() above
        return redirect(url_for('login'))
    return render_template('register12_error.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) :
            login_user(user, remember=form.remember.data)
            # request.args is dictionary type
            next_page = request.args.get('next')
            # 'home' is function of home() above
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else :
            flash('Login failed. Please check email and password.', 'danger')
    return render_template('login13.html', title='Login', form=form)


@app.route("/logout")
def logout() :
    logout_user()
    return redirect(url_for('home'))

# save uploaded image to the specified path
def save_picture(form_picture) :
    random_hex = secrets.token_hex(8)
    # underscore (_) ignoring the value
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    # define the path to store profile image
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
   
    # save the uploaded image into the specified path

    # do not want to save the original uploaded image, which can be very large
    #form_picture.save(picture_path)

    #resize the image before store
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

# login_required decorator makes sure to access the page only
# when the user log in
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account() :
    # this form is for user to update the profile
    form = UpdateAccountForm()
    if form.validate_on_submit() :
        if form.picture.data :
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        # think of current_user is reference to the User in database
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET' :
        # populate the username and email so that
        # the new username and email can be viewed right after 
        # update form is submitted
        form.username.data = current_user.username
        form.email.data = current_user.email
    # user.image_file is defined in User() in models.py from database
    image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
    return render_template('account04.html', title='Account', image_file=image_file, form=form)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post() :
    form = PostForm()
    if form.validate_on_submit():
        # Construct Post object which defined in models.py
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend="New Post")


@app.route("/post/<int:post_id>")
def post(post_id) :
    # find the post or give page not found 404 error
    post = Post.query.get_or_404(post_id)
    return render_template('post02.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id) :
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET' :
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend="Update Post")

# "Delete" button in Modal sends POST request to delete the post
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id) :
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username) :
    page = request.args.get('page', 1, type=int)
    # first_or_404: first user or give 404 if no user is found
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
                    .order_by(Post.date_posted.desc())\
                    .paginate(page=page, per_page=2)
    return render_template('user_posts.html', posts=posts, user=user)


# Send email with the link to reset password
# The URL link is specified by url_for(), route to reset_token()
# _external=True tells Flask that it should generate an absolute URL, and not a relative URL. 
def send_reset_email(user) :
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', 
                   recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


# route the form to send instruction email to request password reset
# when forgot the password
@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request() :
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


# route with the form to set new password (the URL link is from email)
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token) :
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # the token comes with user id. if the user id is valid,
    # the valid user is returned    
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # hash the password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))    
    return render_template('reset_token.html', title='Reset Password', form=form)