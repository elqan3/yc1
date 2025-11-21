from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ------------------ إعدادات المسؤول ------------------
ADMIN_USERNAME = "tyc#admin#1899"
ADMIN_PASSWORD = "0926410278"  # يمكنك تغييره لاحقاً

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("يجب تسجيل الدخول للوصول إلى هذه الصفحة", "warning")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------ صفحة تسجيل دخول المسؤول ------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash("تم تسجيل الدخول بنجاح!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("اسم المستخدم أو كلمة المرور خاطئ", "danger")
            return redirect(url_for('admin_login'))
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("تم تسجيل الخروج", "success")
    return redirect(url_for('admin_login'))

# ------------------ إعداد قاعدة البيانات ------------------
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'members.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ مسارات رفع الملفات ------------------
NEWS_UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'news')
WORK_UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'works')
os.makedirs(NEWS_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WORK_UPLOAD_FOLDER, exist_ok=True)
app.config['NEWS_UPLOAD_FOLDER'] = NEWS_UPLOAD_FOLDER
app.config['WORK_UPLOAD_FOLDER'] = WORK_UPLOAD_FOLDER

# ------------------ النماذج ------------------
class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending / rejected

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    date_published = db.Column(db.DateTime, default=datetime.utcnow)

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ------------------ Routes ------------------
@app.route('/')
def index():
    news_list = News.query.order_by(News.date_published.desc()).all()
    works_list = Work.query.order_by(Work.date_added.desc()).all()
    return render_template("index.html", news_list=news_list, works_list=works_list)

@app.route('/submit_application', methods=['POST'])
def submit_application():
    new_applicant = Applicant(
        full_name=request.form['full_name'],
        age=int(request.form['age']),
        gender=request.form['gender'],
        city=request.form['city'],
        phone=request.form['phone'],
        reason=request.form['reason']
    )
    db.session.add(new_applicant)
    db.session.commit()
    flash("تم إرسال طلبك بنجاح!", "success")
    return redirect(url_for('index'))

# ------------------ لوحة الأدمن ------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/members')
@admin_required
def admin_members():
    applicants = Applicant.query.filter(Applicant.status.in_(['pending', 'rejected'])).all()
    members = Member.query.all()
    return render_template('admin/members.html', applicants=applicants, members=members)

@app.route('/admin/members/accept/<int:applicant_id>')
@admin_required
def accept_applicant(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    member = Member(
        full_name=applicant.full_name,
        age=applicant.age,
        gender=applicant.gender,
        city=applicant.city,
        phone=applicant.phone,
        reason=applicant.reason
    )
    db.session.add(member)
    db.session.delete(applicant)
    db.session.commit()
    return redirect(url_for('admin_members'))

@app.route('/admin/members/reject/<int:applicant_id>')
@admin_required
def reject_applicant(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    if applicant.status == 'pending':
        applicant.status = "rejected"
        db.session.commit()
    return redirect(url_for('admin_members'))

@app.route('/admin/news')
@admin_required
def admin_news():
    news_list = News.query.order_by(News.date_published.desc()).all()
    return render_template('admin/news.html', news_list=news_list)

@app.route('/admin/news/add', methods=['POST'])
@admin_required
def add_news():
    title = request.form['title']
    content = request.form['content']
    image_file = request.files.get('image')

    image_filename = None
    if image_file and image_file.filename != '':
        image_filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['NEWS_UPLOAD_FOLDER'], image_filename))

    new_news = News(title=title, content=content, image_filename=image_filename)
    db.session.add(new_news)
    db.session.commit()
    flash("تم نشر الخبر بنجاح!", "success")
    return redirect(url_for('admin_news'))

@app.route('/admin/news/delete/<int:news_id>')
@admin_required
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash("تم حذف الخبر.", "success")
    return redirect(url_for('admin_news'))

@app.route('/admin/works')
@admin_required
def admin_works():
    works_list = Work.query.order_by(Work.date_added.desc()).all()
    return render_template('admin/works.html', works_list=works_list)

@app.route('/admin/works/add', methods=['POST'])
@admin_required
def add_work():
    title = request.form['title']
    description = request.form['description']
    image_file = request.files.get('image')

    image_filename = None
    if image_file and image_file.filename != '':
        image_filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['WORK_UPLOAD_FOLDER'], image_filename))

    new_work = Work(title=title, description=description, image_filename=image_filename)
    db.session.add(new_work)
    db.session.commit()
    flash("تم إضافة العمل بنجاح!", "success")
    return redirect(url_for('admin_works'))

@app.route('/admin/works/delete/<int:work_id>')
@admin_required
def delete_work(work_id):
    work = Work.query.get_or_404(work_id)
    db.session.delete(work)
    db.session.commit()
    flash("تم حذف العمل.", "success")
    return redirect(url_for('admin_works'))

@app.route('/works')
def works():
    works_list = Work.query.order_by(Work.date_added.desc()).all()
    return render_template('works.html', works_list=works_list)

# ------------------ تشغيل السيرفر ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
