from sqlalchemy import text
from applicationDB import *
from flask_login import current_user

#helper methods
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

def leaderboardContent(qclass_val):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    query = "select  school,class as class_val,section,studentid,student_name,profile_pic,subjectid,test_count,marks from fn_performance_leaderboard_detail_v1("+str(teacher_id.school_id)+")"
    if qclass_val=='dashboard':
        
        where = " where marks is not null order by marks"
        query = query + where
        print('Query inside leaderboardContent:'+str(query))
    else:
        if qclass_val!='' and qclass_val is not None and str(qclass_val)!='None':
            where = " where class='"+str(qclass_val)+"' order by marks desc"
        else:
            where = " where marks is not null order by marks desc"
        query = query + where
        print('Query inside leaderboardContent:'+str(query))    
    leaderbrd_row = db.session.execute(text(query)).fetchall()
    try:
        df = pd.DataFrame(leaderbrd_row,columns=['school','class_val','section','studentid','student_name','profile_pic','subjectid','test_count','marks'])
        
        leaderbrd_pivot = pd.pivot_table(df,index=['studentid','profile_pic','student_name','class_val','section']
                        , columns='subjectid', values='marks'
                        ,aggfunc='sum').reset_index()
        leaderbrd_pivot = leaderbrd_pivot.rename_axis(None).rename_axis(None, axis=1)
        col_list= list(leaderbrd_pivot)
        col_list.remove('studentid')
        col_list.remove('student_name')
        col_list.remove('class_val')
        col_list.remove('section')
        col_list.remove('profile_pic')
        leaderbrd_pivot['total_marks%'] = leaderbrd_pivot[col_list].mean(axis=1)

        # leaderbrd_pivot = leaderbrd_pivot.groupby(['studentid','student_name','class_val','section']).agg()
        df2 = pd.DataFrame(leaderbrd_row,columns=['school','class_val','section','studentid','student_name','profile_pic','subjectid','test_count','marks'])
        leaderbrd_pivot2 = pd.pivot_table(df2,index=['studentid','profile_pic','student_name','class_val','section']
                        , columns='subjectid', values='test_count'
                        ,aggfunc='sum').reset_index()
        leaderbrd_pivot2 = leaderbrd_pivot2.rename_axis(None).rename_axis(None, axis=1)
        col_list2= list(leaderbrd_pivot2)
        col_list2.remove('studentid')
        col_list2.remove('student_name')
        col_list2.remove('class_val')
        col_list2.remove('section')
        col_list2.remove('profile_pic')
        leaderbrd_pivot2['total_tests'] = leaderbrd_pivot2[col_list2].sum(axis=1)
        result = pd.merge(leaderbrd_pivot,leaderbrd_pivot2,on=('studentid','student_name','class_val','section','profile_pic'))
    except:
        result = 1222
    return result  
