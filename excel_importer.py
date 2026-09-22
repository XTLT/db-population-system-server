import os
import pandas as pd
from datetime import datetime
import shutil
import tarfile
import hashlib
import secrets
import json

from config import DB_PATH, BACKUP_DIR, PHOTOS_DIR, EXCEL_TEMPLATE_COLUMNS
from database import get_session, Person, get_db_password, _derive_key, LandSubsidy, TreatmentPayment, PensionInsurance, DibaoPayment, TekunPayment
from utils import safe_str, calculate_age


def _read_excel_robust(file_path: str, header=None):
    """读取 Excel 文件，自动检测格式和引擎"""
    ext = os.path.splitext(file_path)[1].lower()
    engines = (['openpyxl', 'xlrd'] if ext == '.xlsx'
               else ['xlrd', 'openpyxl'] if ext == '.xls'
               else ['openpyxl', 'xlrd'])
    for engine in engines:
        try:
            return pd.read_excel(file_path, dtype=str, header=header, engine=engine)
        except Exception:
            continue
    try:
        return pd.read_csv(file_path, dtype=str, header=header, encoding='utf-8')
    except Exception:
        return pd.read_csv(file_path, dtype=str, header=header, encoding='gbk')


def backup_database(manual: bool = False) -> dict:
    if not os.path.exists(DB_PATH):
        return {"success": False, "error": "数据库文件不存在"}
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        db_backup = os.path.join(backup_dir, "population.db")
        shutil.copy2(DB_PATH, db_backup)
        
        photos_backup = os.path.join(backup_dir, "photos.tar.gz")
        if os.path.exists(PHOTOS_DIR) and os.listdir(PHOTOS_DIR):
            with tarfile.open(photos_backup, "w:gz") as tar:
                tar.add(PHOTOS_DIR, arcname="Photos")
        
        password = get_db_password()
        if password:
            _encrypt_backup(backup_dir, password)
        
        db_hash = _calculate_file_hash(db_backup)
        manifest = {
            "timestamp": timestamp,
            "manual": manual,
            "db_hash": db_hash,
            "encrypted": bool(password),
            "complete": True
        }
        with open(os.path.join(backup_dir, "backup_complete.txt"), "w") as f:
            json.dump(manifest, f)
        
        _cleanup_old_backups()
        
        # 不返回完整路径，防止服务器路径泄露
        return {"success": True, "timestamp": timestamp}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _encrypt_backup(backup_dir: str, password: str):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    
    salt = secrets.token_bytes(32)
    key = _derive_key(password, salt)
    
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath) and filename != "backup_complete.txt":
            with open(filepath, "rb") as f:
                data = f.read()
            nonce = secrets.token_bytes(12)
            aesgcm = AESGCM(key)
            encrypted = aesgcm.encrypt(nonce, data, None)
            with open(filepath + ".enc", "wb") as f:
                f.write(salt + nonce + encrypted)
            os.remove(filepath)


def _calculate_file_hash(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _cleanup_old_backups():
    if not os.path.exists(BACKUP_DIR):
        return
    
    cutoff_date = datetime.now().timestamp() - (60 * 24 * 60 * 60)
    
    for item in os.listdir(BACKUP_DIR):
        item_path = os.path.join(BACKUP_DIR, item)
        if os.path.isdir(item_path) and item.startswith("backup_"):
            try:
                dir_time = os.path.getmtime(item_path)
                if dir_time < cutoff_date:
                    complete_file = os.path.join(item_path, "backup_complete.txt")
                    if os.path.exists(complete_file):
                        shutil.rmtree(item_path)
            except Exception:
                pass


def get_backup_status() -> dict:
    if not os.path.exists(BACKUP_DIR):
        return {"last_backup": None, "status": "无备份"}
    
    backups = []
    for item in os.listdir(BACKUP_DIR):
        if item.startswith("backup_"):
            item_path = os.path.join(BACKUP_DIR, item)
            complete_file = os.path.join(item_path, "backup_complete.txt")
            if os.path.exists(complete_file):
                backups.append({
                    "path": item_path,
                    "time": os.path.getmtime(item_path)
                })
    
    if not backups:
        return {"last_backup": None, "status": "无备份"}
    
    latest = max(backups, key=lambda x: x["time"])
    return {
        "last_backup": datetime.fromtimestamp(latest["time"]).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "正常"
    }


def get_backup_list() -> list:
    """
    获取所有备份列表
    
    Returns:
        备份信息列表，每项包含：
        - timestamp: 备份时间戳
        - time: 格式化时间
        - path: 备份路径
        - size: 备份大小（字节）
        - encrypted: 是否加密
        - manual: 是否手动备份
    """
    if not os.path.exists(BACKUP_DIR):
        return []
    
    backups = []
    for item in os.listdir(BACKUP_DIR):
        if item.startswith("backup_"):
            item_path = os.path.join(BACKUP_DIR, item)
            complete_file = os.path.join(item_path, "backup_complete.txt")
            
            if os.path.exists(complete_file):
                try:
                    with open(complete_file, "r") as f:
                        manifest = json.load(f)
                    
                    # 计算备份大小
                    total_size = 0
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                    
                    backups.append({
                        "timestamp": manifest.get("timestamp", ""),
                        "time": datetime.fromtimestamp(os.path.getmtime(item_path)).strftime("%Y-%m-%d %H:%M:%S"),
                        "name": item,  # 只返回备份目录名，不返回完整路径
                        "size": total_size,
                        "encrypted": manifest.get("encrypted", False),
                        "manual": manifest.get("manual", False)
                    })
                except Exception:
                    pass
    
    # 按时间倒序排列
    backups.sort(key=lambda x: x["time"], reverse=True)
    return backups


def restore_database(backup_path: str, password: str = None) -> dict:
    """
    从备份恢复数据库
    
    Args:
        backup_path: 备份目录路径
        password: 解密密码（如果备份已加密）
    
    Returns:
        恢复结果字典
    """
    if not os.path.exists(backup_path):
        return {"success": False, "error": "备份文件不存在"}
    
    complete_file = os.path.join(backup_path, "backup_complete.txt")
    if not os.path.exists(complete_file):
        return {"success": False, "error": "备份不完整"}
    
    try:
        # 读取清单
        with open(complete_file, "r") as f:
            manifest = json.load(f)
        
        # 如果备份已加密，需要解密
        if manifest.get("encrypted"):
            if not password:
                return {"success": False, "error": "需要解密密码"}
            
            _decrypt_backup(backup_path, password)
        
        # 恢复数据库
        db_backup = os.path.join(backup_path, "population.db")
        if not os.path.exists(db_backup):
            return {"success": False, "error": "数据库备份文件不存在"}
        
        # 备份当前数据库
        current_backup = f"{DB_PATH}.before_restore"
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, current_backup)
        
        # 恢复数据库
        shutil.copy2(db_backup, DB_PATH)
        
        # 恢复照片
        photos_backup = os.path.join(backup_path, "photos.tar.gz")
        if os.path.exists(photos_backup):
            if os.path.exists(PHOTOS_DIR):
                shutil.rmtree(PHOTOS_DIR)
            os.makedirs(PHOTOS_DIR, exist_ok=True)
            
            # 安全解压：防止 Tar Slip 路径遍历攻击
            with tarfile.open(photos_backup, "r:gz") as tar:
                for member in tar.getmembers():
                    # 检查路径是否在允许的目录内
                    member_path = os.path.join(PHOTOS_DIR, member.name)
                    real_member_path = os.path.realpath(os.path.abspath(member_path))
                    
                    # 防止路径遍历
                    if not real_member_path.startswith(os.path.realpath(PHOTOS_DIR)):
                        raise ValueError(f"检测到恶意路径: {member.name}")
                    
                    # 防止绝对路径
                    if member.name.startswith('/') or ':' in member.name:
                        raise ValueError(f"检测到非法路径: {member.name}")
                    
                    # 防止符号链接攻击
                    if member.issym() or member.islnk():
                        raise ValueError("不允许符号链接")
                    
                    tar.extract(member, PHOTOS_DIR)
        
        return {
            "success": True,
            "timestamp": manifest.get("timestamp"),
            "restored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # 清理解密后的文件
        if manifest.get("encrypted"):
            for filename in os.listdir(backup_path):
                if filename.endswith(".db") or filename.endswith(".tar.gz"):
                    filepath = os.path.join(backup_path, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)


def _decrypt_backup(backup_dir: str, password: str):
    """解密备份文件"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    
    for filename in os.listdir(backup_dir):
        if filename.endswith(".enc"):
            filepath = os.path.join(backup_dir, filename)
            with open(filepath, "rb") as f:
                content = f.read()
            
            salt = content[:32]
            nonce = content[32:44]
            encrypted = content[44:]
            
            key = _derive_key(password, salt)
            aesgcm = AESGCM(key)
            data = aesgcm.decrypt(nonce, encrypted, None)
            
            # 写入解密后的文件
            decrypted_path = filepath[:-4]  # 移除 .enc 后缀
            with open(decrypted_path, "wb") as f:
                f.write(data)


def import_excel_full(file_path: str, progress_callback=None) -> dict:
    backup_database()
    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")
    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    session = get_session()
    try:
        session.query(Person).delete()
        session.commit()
        for idx, row in df.iterrows():
            try:
                person = _row_to_person(row, idx)
                session.add(person)
                imported += 1
                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total}


def import_excel_incremental(file_path: str, progress_callback=None) -> dict:
    backup_database()
    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")
    total = len(df)
    imported = 0
    updated = 0
    skipped = 0
    errors = []
    session = get_session()
    try:
        for idx, row in df.iterrows():
            try:
                id_card = safe_str(row.get("身份证号", ""))
                if not id_card:
                    skipped += 1
                    continue
                existing = session.query(Person).filter(Person.id_card == id_card).first()
                if existing:
                    _update_person_from_row(existing, row)
                    updated += 1
                else:
                    person = _row_to_person(row, idx)
                    session.add(person)
                    imported += 1
                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return {"imported": imported, "updated": updated, "skipped": skipped, "errors": errors, "total": total}


def query_persons_with_filters(filters: dict) -> list:
    session = get_session()
    try:
        query = session.query(Person)

        if filters.get("name"):
            query = query.filter(Person.name.contains(filters["name"]))
        if filters.get("address"):
            query = query.filter(Person.address.contains(filters["address"]))
        if filters.get("is_dead") and filters["is_dead"] != "全部":
            query = query.filter(Person.is_dead == filters["is_dead"])
        relation = filters.get("relation", [])
        if relation:
            query = query.filter(Person.relation.in_(relation))
        disability = filters.get("disability", [])
        if disability:
            query = query.filter(Person.disability.in_(disability))
        if filters.get("dis_level"):
            dis_level = filters["dis_level"]
            if isinstance(dis_level, list) and dis_level:
                query = query.filter(Person.dis_level.in_(dis_level))
            elif isinstance(dis_level, str) and dis_level != "全部":
                query = query.filter(Person.dis_level == dis_level)
        poor_type = filters.get("poor_type", [])
        if poor_type:
            query = query.filter(Person.poor_type.in_(poor_type))
        if filters.get("dibao") and filters["dibao"] != "全部":
            query = query.filter(Person.dibao == filters["dibao"])
        if filters.get("tekun") and filters["tekun"] != "全部":
            query = query.filter(Person.tekun == filters["tekun"])
        if filters.get("jisheng") and filters["jisheng"] != "全部":
            query = query.filter(Person.jisheng == filters["jisheng"])
        land = filters.get("land_area", "全部")
        if land == "不为0":
            query = query.filter(Person.land_area != "", Person.land_area.isnot(None))
        elif land == "空白":
            query = query.filter(
                (Person.land_area == "") | (Person.land_area.is_(None))
            )

        persons = query.all()

        if filters.get("age_min") or filters.get("age_max"):
            age_min = int(filters["age_min"]) if filters.get("age_min") else 0
            age_max = int(filters["age_max"]) if filters.get("age_max") else 999
            filtered = []
            for p in persons:
                age = -1
                if p.age:
                    try:
                        age = int(p.age)
                    except (ValueError, TypeError):
                        pass
                if age < 0 and p.id_card:
                    age_str = calculate_age(p.id_card)
                    if age_str:
                        try:
                            age = int(age_str)
                        except (ValueError, TypeError):
                            pass
                if age >= 0 and age_min <= age <= age_max:
                    filtered.append(p)
            persons = filtered

        return persons
    finally:
        session.close()


def export_excel(file_path: str, progress_callback=None, filters: dict = None) -> bool:
    if filters:
        persons = query_persons_with_filters(filters)
    else:
        session = get_session()
        try:
            persons = session.query(Person).all()
        finally:
            session.close()

    if not persons:
        return False

    data = []
    for i, p in enumerate(persons):
        data.append({
            "户号": p.hu_hao,
            "身份证号": p.id_card,
            "姓名": p.name,
            "地址": p.address,
            "与户主关系": p.relation,
            "是否死亡": p.is_dead,
            "电话": p.phone,
            "备注": p.remark,
            "脱贫户或监测户": p.poor_type,
            "残疾": p.disability,
            "残疾等级": p.dis_level,
            "低保": p.dibao,
            "特困供养": p.tekun,
            "供养类型": p.tekun_type,
            "是否计生家庭": p.jisheng,
            "社保卡号1": p.social_card1,
            "社保卡号2": p.social_card2,
            "社保卡号3": p.social_card3,
            "土地面积": p.land_area or "",
        })
        if progress_callback and (i + 1) % 100 == 0:
            progress_callback(int((i + 1) / len(persons) * 100))
    df = pd.DataFrame(data, columns=EXCEL_TEMPLATE_COLUMNS)
    df.to_excel(file_path, index=False, engine="openpyxl")
    return True


def generate_template(file_path: str):
    df = pd.DataFrame(columns=EXCEL_TEMPLATE_COLUMNS)
    df.to_excel(file_path, index=False, engine="openpyxl")


def _row_to_person(row, idx) -> Person:
    id_card = safe_str(row.get("身份证号", ""))
    return Person(
        id=f"p_{idx}_{id_card}",
        hu_hao=safe_str(row.get("户号", "")),
        id_card=id_card,
        name=safe_str(row.get("姓名", "")),
        age=calculate_age(id_card),
        address=safe_str(row.get("地址", "")),
        relation=safe_str(row.get("与户主关系", "")),
        is_dead=safe_str(row.get("是否死亡", "否")),
        phone=safe_str(row.get("电话", "")),
        remark=safe_str(row.get("备注", "")),
        poor_type=safe_str(row.get("脱贫户或监测户", "")),
        disability=safe_str(row.get("残疾", "")),
        dis_level=safe_str(row.get("残疾等级", "")),
        dibao=safe_str(row.get("低保", "")),
        tekun=safe_str(row.get("特困供养", "")),
        tekun_type=safe_str(row.get("供养类型", "")),
        jisheng=safe_str(row.get("是否计生家庭", "")),
        social_card1=safe_str(row.get("社保卡号1", "")),
        social_card2=safe_str(row.get("社保卡号2", "")),
        social_card3=safe_str(row.get("社保卡号3", "")),
        land_area=safe_str(row.get("土地面积", "")),
    )


def _update_person_from_row(person: Person, row):
    person.hu_hao = safe_str(row.get("户号", person.hu_hao))
    person.name = safe_str(row.get("姓名", person.name))
    person.age = calculate_age(person.id_card)
    person.address = safe_str(row.get("地址", person.address))
    person.relation = safe_str(row.get("与户主关系", person.relation))
    person.is_dead = safe_str(row.get("是否死亡", person.is_dead))
    person.phone = safe_str(row.get("电话", person.phone))
    person.remark = safe_str(row.get("备注", person.remark))
    person.poor_type = safe_str(row.get("脱贫户或监测户", person.poor_type))
    person.disability = safe_str(row.get("残疾", person.disability))
    person.dis_level = safe_str(row.get("残疾等级", person.dis_level))
    person.dibao = safe_str(row.get("低保", person.dibao))
    person.tekun = safe_str(row.get("特困供养", person.tekun))
    person.tekun_type = safe_str(row.get("供养类型", person.tekun_type))
    person.jisheng = safe_str(row.get("是否计生家庭", person.jisheng))
    person.social_card1 = safe_str(row.get("社保卡号1", person.social_card1))
    person.social_card2 = safe_str(row.get("社保卡号2", person.social_card2))
    person.social_card3 = safe_str(row.get("社保卡号3", person.social_card3))
    person.land_area = safe_str(row.get("土地面积", person.land_area))


def import_land_subsidy(file_path: str, subsidy_year: str = "", progress_callback=None) -> dict:

    df = _read_excel_robust(file_path, header=None)
    df = df.fillna("")

    header_row = -1
    for idx, row in df.iterrows():
        values = [str(v).strip() for v in row.values]
        if "姓名" in values and "身份证号" in values:
            header_row = idx
            break

    if header_row == -1:
        return {"imported": 0, "skipped": 0, "errors": ["未找到表头（姓名、身份证号）"], "total": 0}

    main_headers = [str(v).strip() for v in df.iloc[header_row].values]

    # 检查是否需要处理副表头
    # 如果下一行的第一个单元格是数字（如补贴年度）或身份证号格式，则认为是数据行，不需要副表头
    use_sub_header = False
    if header_row + 1 < len(df):
        next_row = [str(v).strip() for v in df.iloc[header_row + 1].values]
        # 检查下一行是否是数据行（通常数据行的补贴年度是年份，身份证号是数字）
        # 如果下一行不包含"姓名"、"身份证号"等表头关键词，则认为是数据行
        header_keywords = ["姓名", "身份证", "补贴", "面积", "金额", "标准"]
        has_header_keyword = any(kw in " ".join(next_row) for kw in header_keywords)
        if has_header_keyword:
            use_sub_header = True
            sub_headers = next_row
        else:
            sub_headers = [""] * len(main_headers)
    else:
        sub_headers = [""] * len(main_headers)

    col_map = {}
    for i, (main, sub) in enumerate(zip(main_headers, sub_headers)):
        if main:
            if sub:
                col_map[i] = f"{main}_{sub}"
            else:
                col_map[i] = main
        elif sub:
            col_map[i] = sub
        else:
            col_map[i] = f"col_{i}"

    # 根据是否使用副表头，决定数据起始行
    data_start_row = header_row + 2 if use_sub_header else header_row + 1
    data_df = df.iloc[data_start_row:].reset_index(drop=True)
    data_df.columns = [col_map.get(i, f"col_{i}") for i in range(len(col_map))]

    total = len(data_df)
    imported = 0
    skipped = 0
    errors = []
    session = get_session()

    try:
        for idx, row in data_df.iterrows():
            try:
                name = safe_str(row.get("姓名", ""))
                id_card = safe_str(row.get("身份证号", ""))

                if not name and not id_card:
                    skipped += 1
                    continue

                certified_area = ""
                for key in row.index:
                    if "确权颁证面积" in key or "确权颁发面积" in key:
                        certified_area = safe_str(row.get(key, ""))
                        break

                subsidy_area = ""
                for key in row.index:
                    if "补贴面积" in key:
                        val = safe_str(row.get(key, ""))
                        subsidy_area = val.replace("（亩）", "").replace("(亩)", "").strip()
                        break

                base_standard = ""
                for key in row.index:
                    if "基础补贴标准" in key:
                        val = safe_str(row.get(key, ""))
                        base_standard = val.replace("（元/亩）", "").replace("(元/亩)", "").strip()
                        break

                rape_area = ""
                for key in row.index:
                    if "其中种植油菜" in key and "面积" in key:
                        rape_area = safe_str(row.get(key, "")).strip()
                        break

                rape_amount = ""
                for key in row.index:
                    if "其中种植油菜" in key and "金额" in key:
                        rape_amount = safe_str(row.get(key, "")).strip()
                        break

                total_amount = ""
                for key in row.index:
                    if "补贴总金额" in key:
                        val = safe_str(row.get(key, ""))
                        total_amount = val.replace("（元）", "").replace("(元)", "").strip()
                        break

                subsidy = LandSubsidy(
                    id=f"ls_{secrets.token_hex(8)}",
                    id_card=id_card,
                    name=name,
                    subsidy_year=subsidy_year,
                    certified_area=certified_area,
                    subsidy_area=subsidy_area,
                    base_standard=base_standard,
                    rape_area=rape_area,
                    rape_amount=rape_amount,
                    total_amount=total_amount,
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                session.add(subsidy)
                imported += 1

                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + header_row + 3}: {str(e)}")

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total}


def get_all_land_subsidies(subsidy_year: str = None) -> list:

    session = get_session()
    try:
        query = session.query(LandSubsidy)
        if subsidy_year:
            query = query.filter(LandSubsidy.year == subsidy_year)
        return query.order_by(LandSubsidy.name).all()
    finally:
        session.close()


def delete_land_subsidy(subsidy_id: str):

    session = get_session()
    try:
        subsidy = session.query(LandSubsidy).filter(LandSubsidy.id == subsidy_id).first()
        if subsidy:
            session.delete(subsidy)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_person_subsidy_total(id_card: str, subsidy_year: str = None) -> str:

    session = get_session()
    try:
        query = session.query(LandSubsidy).filter(LandSubsidy.id_card == id_card)
        if subsidy_year:
            query = query.filter(LandSubsidy.year.startswith(subsidy_year))
        subsidies = query.all()
        if not subsidies:
            return ""
        total = 0.0
        for s in subsidies:
            try:
                total += float(s.total_amount)
            except (ValueError, TypeError):
                pass
        return f"{total:.2f}" if total > 0 else ""
    finally:
        session.close()


def get_year_subsidy_totals() -> dict:

    session = get_session()
    try:
        subsidies = session.query(LandSubsidy).all()
        totals = {}
        for s in subsidies:
            year = s.year or "未知"
            if year not in totals:
                totals[year] = 0.0
            try:
                totals[year] += float(s.total_amount)
            except (ValueError, TypeError):
                pass
        return totals
    finally:
        session.close()


def import_treatment_payment(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入待遇发放数据，支持三种表格格式：
    1. 待遇发放成功信息表：包含所属乡镇、所属村、费款所属期、支付标志、个人编号、公民身份证号码、姓名、银行账号、金额、失败原因
    2. 待遇支付信息表：包含所属乡镇、所属村、费款所属期、姓名、公民身份证号码、银行账号、金额、支付标志
    3. 低保特困发放台账：包含救助类型、人员姓名、人员身份证号、和申请人关系、家庭保障总金额
    
    只导入身份证号在数据库中存在的人员
    """

    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    # 检测表格类型
    columns = list(df.columns)
    file_name = os.path.basename(file_path)

    # 格式3：低保特困发放台账
    has_format3 = "救助类型" in columns and "人员身份证号" in columns

    # 确定姓名和身份证列名
    name_col = None
    id_card_col = None
    amount_col = None

    if has_format3:
        name_col = "人员姓名"
        id_card_col = "人员身份证号"
        amount_col = "家庭保障总金额"
    elif "姓名" in columns:
        name_col = "姓名"
        if "公民身份证号码" in columns:
            id_card_col = "公民身份证号码"
        elif "身份证号" in columns:
            id_card_col = "身份证号"
        amount_col = "金额" if "金额" in columns else None

    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}

    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    not_found = []
    session = get_session()

    # 获取数据库中所有身份证号
    existing_id_cards = set()
    try:
        persons = session.query(Person.id_card).all()
        existing_id_cards = {p.id_card for p in persons if p.id_card}
    except Exception:
        pass

    try:
        for idx, row in df.iterrows():
            try:
                name = safe_str(row.get(name_col, ""))
                if not name:
                    skipped += 1
                    continue

                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""
                
                # 检查身份证号是否在数据库中存在
                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    skipped += 1
                    continue
                
                amount = safe_str(row.get(amount_col, "")) if amount_col else ""

                # 根据表格类型提取其他字段
                town = safe_str(row.get("所属乡镇", ""))
                village = safe_str(row.get("所属村", ""))
                row_period = safe_str(row.get("费款所属期", "")) or period
                payment_status = safe_str(row.get("支付标志", ""))
                personal_code = safe_str(row.get("个人编号", ""))
                bank_account = safe_str(row.get("银行账号", ""))
                fail_reason = safe_str(row.get("失败原因", ""))
                subsidy_type = safe_str(row.get("救助类型", ""))
                relation = safe_str(row.get("和申请人关系", ""))

                payment = TreatmentPayment(
                    id=f"tp_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=town,
                    village=village,
                    period=row_period,
                    payment_status=payment_status,
                    personal_code=personal_code,
                    bank_account=bank_account,
                    amount=amount,
                    subsidy_type=subsidy_type,
                    relation=relation,
                    fail_reason=fail_reason,
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    import_source=file_name,
                )
                session.add(payment)
                imported += 1

                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total, "not_found": not_found}


def get_all_treatment_payments(period: str = None, id_card: str = None, subsidy_type: str = None) -> list:

    session = get_session()
    try:
        query = session.query(TreatmentPayment)
        if period:
            query = query.filter(TreatmentPayment.period == period)
        if id_card:
            safe_id_card = id_card.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            query = query.filter(TreatmentPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if subsidy_type:
            query = query.filter(TreatmentPayment.subsidy_type == subsidy_type)
        return query.order_by(TreatmentPayment.period.desc(), TreatmentPayment.name).all()
    finally:
        session.close()


def delete_treatment_payment(payment_id: str):

    session = get_session()
    try:
        payment = session.query(TreatmentPayment).filter(TreatmentPayment.id == payment_id).first()
        if payment:
            session.delete(payment)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# API 别名函数
def import_treatment_payment_excel(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入待遇发放数据 - API 别名"""
    return import_treatment_payment(file_path, progress_callback, period=period)


def import_land_subsidy_excel(file_path: str, subsidy_year: str = "", progress_callback=None) -> dict:
    """导入地力补贴数据
    
    只导入身份证号在数据库中存在的人员
    
    Args:
        file_path: Excel 文件路径
        subsidy_year: 补贴年份
        progress_callback: 进度回调函数
    
    Returns:
        导入结果字典
    """
    
    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")
    
    columns = list(df.columns)
    
    # 确定列名映射
    name_col = None
    id_card_col = None
    area_col = None
    amount_col = None
    
    if "姓名" in columns:
        name_col = "姓名"
    elif "承包人姓名" in columns:
        name_col = "承包人姓名"
    
    if "身份证号" in columns:
        id_card_col = "身份证号"
    elif "身份证号码" in columns:
        id_card_col = "身份证号码"
    elif "公民身份证号码" in columns:
        id_card_col = "公民身份证号码"
    
    if "确权面积" in columns:
        area_col = "确权面积"
    elif "耕地面积" in columns:
        area_col = "耕地面积"
    elif "土地面积" in columns:
        area_col = "土地面积"
    
    if "补贴金额" in columns:
        amount_col = "补贴金额"
    elif "总金额" in columns:
        amount_col = "总金额"
    elif "合计金额" in columns:
        amount_col = "合计金额"
    
    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}
    
    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    not_found = []
    session = get_session()

    # 获取数据库中所有身份证号
    existing_id_cards = set()
    try:
        persons = session.query(Person.id_card).all()
        existing_id_cards = {p.id_card for p in persons if p.id_card}
    except Exception:
        pass
    
    try:
        for idx, row in df.iterrows():
            try:
                name = safe_str(row.get(name_col, ""))
                if not name:
                    skipped += 1
                    continue
                
                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""
                
                # 检查身份证号是否在数据库中存在
                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    skipped += 1
                    continue
                
                land_area = safe_str(row.get(area_col, "")) if area_col else ""
                subsidy_amount = safe_str(row.get(amount_col, "")) if amount_col else ""
                
                # 其他可能的字段
                certified_area = safe_str(row.get("确权面积", ""))
                subsidy_area = safe_str(row.get("补贴面积", ""))
                base_standard = safe_str(row.get("补贴标准", ""))
                rape_area = safe_str(row.get("油菜面积", ""))
                rape_amount = safe_str(row.get("油菜金额", ""))
                total_amount = safe_str(row.get("总金额", ""))
                
                subsidy = LandSubsidy(
                    id=f"ls_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    year=subsidy_year,
                    land_area=land_area,
                    subsidy_amount=subsidy_amount or total_amount,
                    certified_area=certified_area,
                    subsidy_area=subsidy_area,
                    base_standard=base_standard,
                    rape_area=rape_area,
                    rape_amount=rape_amount,
                    total_amount=total_amount,
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                session.add(subsidy)
                imported += 1
                
                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")
        
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    
    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total, "not_found": not_found}


def import_pension_insurance_excel(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入养老保险数据
    
    只导入身份证号在数据库中存在的人员
    
    Args:
        file_path: Excel 文件路径
        progress_callback: 进度回调函数
        period: 费款所属期（如Excel中无此列则使用此值）
    
    Returns:
        导入结果字典
    """
    
    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")
    
    columns = list(df.columns)
    file_name = os.path.basename(file_path)
    
    # 验证必需列
    if "姓名" not in columns:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}
    
    # 确定身份证列名
    id_card_col = None
    if "公民身份证号码" in columns:
        id_card_col = "公民身份证号码"
    elif "身份证号" in columns:
        id_card_col = "身份证号"
    elif "身份证号码" in columns:
        id_card_col = "身份证号码"
    
    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    not_found = []
    session = get_session()

    # 获取数据库中所有身份证号
    existing_id_cards = set()
    try:
        persons = session.query(Person.id_card).all()
        existing_id_cards = {p.id_card for p in persons if p.id_card}
    except Exception:
        pass
    
    try:
        for idx, row in df.iterrows():
            try:
                name = safe_str(row.get("姓名", ""))
                if not name:
                    skipped += 1
                    continue
                
                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""
                
                # 检查身份证号是否在数据库中存在
                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    skipped += 1
                    continue
                
                pension = PensionInsurance(
                    id=f"pi_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=safe_str(row.get("所属乡镇", "")),
                    village=safe_str(row.get("所属村", "")),
                    period=safe_str(row.get("费款所属期", "")) or period,
                    payment_status=safe_str(row.get("支付标志", "")),
                    personal_code=safe_str(row.get("个人编号", "")),
                    person_id=safe_str(row.get("享受定期待遇人员ID", "")),
                    bank_account=safe_str(row.get("银行账号", "")),
                    amount=safe_str(row.get("金额", "")),
                    fail_reason=safe_str(row.get("失败原因", "")),
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    import_source=file_name,
                )
                session.add(pension)
                imported += 1
                
                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")
        
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    
    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total, "not_found": not_found}


def import_dibao_payment_excel(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入低保发放数据
    
    支持两种Excel格式：
    1. 低保特困发放台账：包含救助类型列，只导入救助类型包含'低保'的记录
    2. 通用格式：包含姓名/人员姓名、身份证号、金额/家庭保障总金额
    
    只导入身份证号在数据库中存在的人员
    period: 用户指定的费款所属期，Excel中无费款所属期列时使用
    """

    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    columns = list(df.columns)
    file_name = os.path.basename(file_path)

    has_subsidy_type = "救助类型" in columns and "人员身份证号" in columns

    name_col = None
    id_card_col = None
    amount_col = None

    if has_subsidy_type:
        name_col = "人员姓名" if "人员姓名" in columns else "姓名"
        id_card_col = "人员身份证号"
        amount_col = "家庭保障总金额"
    elif "姓名" in columns:
        name_col = "姓名"
        if "公民身份证号码" in columns:
            id_card_col = "公民身份证号码"
        elif "身份证号" in columns:
            id_card_col = "身份证号"
        elif "身份证号码" in columns:
            id_card_col = "身份证号码"
        amount_col = "金额" if "金额" in columns else None

    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}

    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    not_found = []
    session = get_session()

    existing_id_cards = set()
    try:
        persons = session.query(Person.id_card).all()
        existing_id_cards = {p.id_card for p in persons if p.id_card}
    except Exception:
        pass

    try:
        for idx, row in df.iterrows():
            try:
                name = safe_str(row.get(name_col, ""))
                if not name:
                    skipped += 1
                    continue

                # 低保特困台账格式：过滤只导入低保记录
                if has_subsidy_type:
                    subsidy_type = safe_str(row.get("救助类型", ""))
                    if "低保" not in subsidy_type and "最低生活保障" not in subsidy_type:
                        skipped += 1
                        continue

                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""

                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    skipped += 1
                    continue

                amount = safe_str(row.get(amount_col, "")) if amount_col else ""

                record = DibaoPayment(
                    id=f"db_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=safe_str(row.get("所属乡镇", "")),
                    village=safe_str(row.get("所属村", "")),
                    period=safe_str(row.get("费款所属期", "")) or period,
                    payment_status=safe_str(row.get("支付标志", "")),
                    personal_code=safe_str(row.get("个人编号", "")),
                    bank_account=safe_str(row.get("银行账号", "")),
                    amount=amount,
                    relation=safe_str(row.get("和申请人关系", "")),
                    fail_reason=safe_str(row.get("失败原因", "")),
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    import_source=file_name,
                )
                session.add(record)
                imported += 1

                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total, "not_found": not_found}


def import_tekun_payment_excel(file_path: str, progress_callback=None, period: str = "") -> dict:
    """导入特困发放数据
    
    支持两种Excel格式：
    1. 低保特困发放台账：包含救助类型列，只导入救助类型包含'特困'的记录
    2. 通用格式：包含姓名/人员姓名、身份证号、金额/家庭保障总金额
    
    只导入身份证号在数据库中存在的人员
    period: 用户指定的费款所属期，Excel中无费款所属期列时使用
    """

    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")

    columns = list(df.columns)
    file_name = os.path.basename(file_path)

    has_subsidy_type = "救助类型" in columns and "人员身份证号" in columns

    name_col = None
    id_card_col = None
    amount_col = None

    if has_subsidy_type:
        name_col = "人员姓名" if "人员姓名" in columns else "姓名"
        id_card_col = "人员身份证号"
        amount_col = "家庭保障总金额"
    elif "姓名" in columns:
        name_col = "姓名"
        if "公民身份证号码" in columns:
            id_card_col = "公民身份证号码"
        elif "身份证号" in columns:
            id_card_col = "身份证号"
        elif "身份证号码" in columns:
            id_card_col = "身份证号码"
        amount_col = "金额" if "金额" in columns else None

    if not name_col:
        return {"imported": 0, "skipped": 0, "errors": ["未找到姓名列"], "total": 0, "not_found": []}

    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    not_found = []
    session = get_session()

    existing_id_cards = set()
    try:
        persons = session.query(Person.id_card).all()
        existing_id_cards = {p.id_card for p in persons if p.id_card}
    except Exception:
        pass

    try:
        for idx, row in df.iterrows():
            try:
                name = safe_str(row.get(name_col, ""))
                if not name:
                    skipped += 1
                    continue

                # 低保特困台账格式：过滤只导入特困记录
                if has_subsidy_type:
                    subsidy_type = safe_str(row.get("救助类型", ""))
                    if "特困" not in subsidy_type:
                        skipped += 1
                        continue

                id_card = safe_str(row.get(id_card_col, "")) if id_card_col else ""

                if id_card and id_card not in existing_id_cards:
                    not_found.append(f"{name}({id_card})")
                    skipped += 1
                    continue

                amount = safe_str(row.get(amount_col, "")) if amount_col else ""

                record = TekunPayment(
                    id=f"tk_{secrets.token_hex(8)}",
                    name=name,
                    id_card=id_card,
                    town=safe_str(row.get("所属乡镇", "")),
                    village=safe_str(row.get("所属村", "")),
                    period=safe_str(row.get("费款所属期", "")) or period,
                    payment_status=safe_str(row.get("支付标志", "")),
                    personal_code=safe_str(row.get("个人编号", "")),
                    bank_account=safe_str(row.get("银行账号", "")),
                    amount=amount,
                    relation=safe_str(row.get("和申请人关系", "")),
                    fail_reason=safe_str(row.get("失败原因", "")),
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    import_source=file_name,
                )
                session.add(record)
                imported += 1

                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total, "not_found": not_found}
