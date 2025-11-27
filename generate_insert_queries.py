#!/usr/bin/env python3
"""
엑셀 파일의 데이터를 Oracle DB INSERT 쿼리로 변환하는 스크립트
"""
import pandas as pd
from openpyxl import load_workbook
import sys
import os

def escape_sql_string(value):
    """SQL 문자열 이스케이프 처리"""
    if pd.isna(value) or value is None:
        return 'NULL'
    if isinstance(value, (int, float)):
        return str(value)
    # 문자열인 경우 작은따옴표 이스케이프
    value_str = str(value).replace("'", "''")
    return f"'{value_str}'"

def get_oracle_type(pandas_type, excel_type=None):
    """Pandas 타입을 Oracle 타입으로 변환"""
    if excel_type and 'VARCHAR' in str(excel_type).upper():
        return str(excel_type)
    if pandas_type == 'int64':
        return 'NUMBER'
    elif pandas_type == 'float64':
        return 'NUMBER'
    elif pandas_type == 'object':
        return 'VARCHAR2(4000)'
    elif 'datetime' in str(pandas_type):
        return 'DATE'
    else:
        return 'VARCHAR2(4000)'

def convert_to_oracle_type(excel_type):
    """엑셀의 타입을 Oracle 타입으로 변환"""
    if pd.isna(excel_type):
        return 'VARCHAR2(4000)'
    
    excel_type = str(excel_type).strip().upper()
    
    # DATETIME을 TIMESTAMP로 변환
    if 'DATETIME' in excel_type:
        return 'TIMESTAMP'
    elif 'INTEGER' in excel_type or 'INT' in excel_type:
        return 'NUMBER'
    elif 'VARCHAR' in excel_type:
        return excel_type.replace('VARCHAR', 'VARCHAR2')
    elif 'CHAR' in excel_type:
        return excel_type.replace('CHAR', 'CHAR')
    else:
        return excel_type

def generate_create_table(df, table_name='INFORMNOTE_TABLE'):
    """CREATE TABLE 쿼리 생성"""
    columns = []
    
    for _, row in df.iterrows():
        col_name = str(row['컬럼명']).strip()
        col_type = str(row['타입']).strip()
        is_pk = str(row['PK']).strip().upper() == 'PK'
        nullable = str(row['Nullable']).strip().upper() == 'Y'
        
        if pd.isna(col_name) or col_name == 'nan' or col_name == '컬럼명':
            continue
        
        # Oracle 타입으로 변환
        oracle_type = convert_to_oracle_type(col_type)
            
        # NULL 제약조건
        null_constraint = '' if nullable else ' NOT NULL'
        columns.append(f"    {col_name} {oracle_type}{null_constraint}")
    
    # PK 제약조건 찾기
    pk_columns = []
    for _, row in df.iterrows():
        if str(row['PK']).strip().upper() == 'PK':
            pk_col = str(row['컬럼명']).strip()
            if pk_col and pk_col != 'nan' and pk_col != '컬럼명':
                pk_columns.append(pk_col)
    
    pk_constraint = ''
    if pk_columns:
        pk_constraint = f",\n    CONSTRAINT {table_name}_PK PRIMARY KEY ({', '.join(pk_columns)})"
    
    create_sql = f"""CREATE TABLE {table_name} (
{',\n'.join(columns)}{pk_constraint}
);"""
    
    return create_sql

def is_table_definition_sheet(df):
    """테이블 정의서인지 확인 (컬럼명, 타입, PK 등의 컬럼이 있는지)"""
    columns = [str(col).lower() for col in df.columns]
    definition_keywords = ['컬럼명', '타입', 'pk', 'nullable', '설명']
    return any(keyword in ' '.join(columns) for keyword in definition_keywords)

def generate_insert_queries_from_data_file(excel_file, table_name='INFORMNOTE_TABLE'):
    """실제 데이터 파일에서 INSERT 쿼리 생성"""
    try:
        # 데이터 파일 읽기 (첫 행이 헤더)
        df_data = pd.read_excel(excel_file, engine='openpyxl', header=0)
        
        if df_data.empty:
            return []
        
        column_names = list(df_data.columns)
        insert_queries = []
        
        for _, row in df_data.iterrows():
            value_list = []
            for col_name in column_names:
                value = row[col_name]
                value_list.append(escape_sql_string(value))
            
            # 모든 값이 NULL이 아닌 경우만 추가
            if any(v != 'NULL' for v in value_list):
                insert_query = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(value_list)});"
                insert_queries.append(insert_query)
        
        return insert_queries
    except Exception as e:
        print(f"데이터 파일 읽기 오류: {e}")
        return []

def generate_insert_queries(df, table_name='INFORMNOTE_TABLE', excel_file=None):
    """INSERT 쿼리 생성 - 테이블 정의서인 경우 빈 리스트 반환"""
    # 테이블 정의서인 경우 INSERT 쿼리 생성 안 함
    if is_table_definition_sheet(df):
        print("테이블 정의서로 확인되었습니다. INSERT 쿼리는 생성하지 않습니다.")
        print("실제 데이터가 있는 별도의 엑셀 파일이 필요합니다.")
        return []
    
    # 실제 데이터 파일인 경우
    if excel_file:
        return generate_insert_queries_from_data_file(excel_file, table_name)
    
    return []

def main():
    """메인 함수"""
    excel_file = 'data_table.xlsx'
    
    if not os.path.exists(excel_file):
        # .csv 확장자 파일도 시도
        if os.path.exists('data_table.csv'):
            excel_file = 'data_table.csv'
        else:
            print(f"오류: {excel_file} 파일을 찾을 수 없습니다.")
            sys.exit(1)
    
    print(f"엑셀 파일 읽기: {excel_file}")
    df = pd.read_excel(excel_file, engine='openpyxl')
    
    print(f"\n데이터 행 수: {len(df)}")
    print(f"컬럼: {list(df.columns)}")
    
    # 테이블명 입력 받기 (기본값: INFORMNOTE_TABLE)
    table_name = input("\n테이블명을 입력하세요 (기본값: INFORMNOTE_TABLE): ").strip()
    if not table_name:
        table_name = 'INFORMNOTE_TABLE'
    
    # CREATE TABLE 쿼리 생성
    print("\n=== CREATE TABLE 쿼리 ===")
    create_sql = generate_create_table(df, table_name)
    print(create_sql)
    
    # INSERT 쿼리 생성
    print("\n=== INSERT 쿼리 ===")
    is_definition = is_table_definition_sheet(df)
    
    if is_definition:
        print("현재 파일은 테이블 정의서입니다.")
        data_file = input("실제 데이터가 있는 엑셀 파일 경로를 입력하세요 (없으면 Enter): ").strip()
        if data_file and os.path.exists(data_file):
            insert_queries = generate_insert_queries(df, table_name, data_file)
        else:
            insert_queries = []
    else:
        insert_queries = generate_insert_queries(df, table_name, excel_file)
    
    if insert_queries:
        print(f"총 {len(insert_queries)}개의 INSERT 쿼리가 생성되었습니다.\n")
        for i, query in enumerate(insert_queries[:10], 1):  # 처음 10개만 출력
            print(f"-- {i}번째 행")
            print(query)
        if len(insert_queries) > 10:
            print(f"\n... 외 {len(insert_queries) - 10}개 쿼리 생략 (파일에는 모두 저장됨)")
    else:
        print("INSERT할 데이터가 없습니다.")
    
    # 파일로 저장
    output_file = f'{table_name}_queries.sql'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"-- {table_name} 테이블 생성 및 데이터 삽입 쿼리\n")
        f.write(f"-- 생성일: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(create_sql)
        f.write("\n\n")
        
        if insert_queries:
            f.write("-- 데이터 삽입\n")
            for query in insert_queries:
                f.write(query + "\n")
    
    print(f"\n쿼리가 {output_file} 파일에 저장되었습니다.")

if __name__ == '__main__':
    main()

