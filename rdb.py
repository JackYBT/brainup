import pymysql
import json
from datetime import datetime


def connect_naolu_db(status):
    if status == 'test':
        return pymysql.connect(host='rm-2zekh662e75ybua3zxo.mysql.rds.aliyuncs.com',
                           port=3306,
                           user='root',
                           password='Naolu_database_test',
                           database='psychic_health_backend'
                           )
    # else:
    #     return pymysql.connect(host='rm-2zetup3n8207q9c2a7o.mysql.rds.aliyuncs.com',
    #                        port=3306,
    #                        user='root',
    #                        password='Naolu_database',
    #                        database='naolu_brain'
    #                        )


def insert_analysis_rec(db,userid,report_id,status, data):
    con = connect_naolu_db(db)
    cur = con.cursor()

    try:
        sql_str = (
            "INSERT INTO `phb_analysis_data` " +
            "(create_time,create_user,update_time,update_user,report_id,status,n_chal,freq_theta_b," +
            "freq_theta_s,freq_alpha_b,freq_alpha_s,freq_beta_b,amplitude_theta,amplitude_alpha,amplitude_beta," +
            "freq_beta_s,d_order_all_new_alpha,d_order_all_new_beta,d_order_all_new_theta) " +
            "VALUES ('%s','%d','%s','%d','%d','%d','%d','%.5f','%.5f','%.5f','%.5f','%.5f','%.5f','%.5f','%.5f','%.5f','%.5f','%.5f','%.5f')" % (
                str(datetime.now()),
                userid,
                str(datetime.now()),
                userid,
                int(report_id),
                status,
                data["n_chal"],
                data["freq_theta_b"],
                data["freq_theta_s"],
                data["freq_alpha_b"],
                data["freq_alpha_s"],
                data["freq_beta_b"],
                data["amplitude_theta"],
                data["amplitude_alpha"],
                data["amplitude_beta"],
                data["freq_beta_s"],
                data["d_order_all_new_alpha"],
                data["d_order_all_new_beta"],
                data["d_order_all_new_theta"]
            )
        )
        cur.execute(sql_str)
        con.commit()
        print("write data to db OK",report_id)
    except:
        con.rollback()
        print('Insert operation error')
        # raise
    finally:
        cur.close()
        con.close()
