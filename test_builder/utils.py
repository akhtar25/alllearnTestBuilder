from sqlalchemy import text
from applicationDB import *
from flask_login import current_user

def classSecCheck():
    teacherProfile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #print('#######this is teacher profile val '+ str(teacherProfile.teacher_id))
    #print('#######this is current user '+ str(current_user.id))
    if teacherProfile==None:
        return 'N'
    else:
        classSecRow = ClassSection.query.filter_by(school_id=teacherProfile.school_id).all()
        #print(classSecRow)
        if len(classSecRow)==0:
            print('returning N')
            return 'N'            
        else:
            return 'Y' 

def schoolNameVal():
    if current_user.is_authenticated:
        teacher_id = ''
        if current_user.user_type==134 or current_user.user_type==234:
            teacher_id = StudentProfile.query.filter_by(user_id=current_user.id).first()
        else:
            teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()        
        if teacher_id != None:
            print(teacher_id.school_id)
            school_name_row=SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
            if school_name_row!=None:
                name=school_name_row.school_name            
                return name
            else:
                return None            
        else:
            return None
    else:
        return None