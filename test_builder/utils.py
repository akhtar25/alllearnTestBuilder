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