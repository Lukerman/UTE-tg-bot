import os
from pymongo import MongoClient
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI) if MONGO_URI else None
db = client.file_monetization if client is not None else None

users_collection = db.users if db is not None else None
files_collection = db.files if db is not None else None
views_collection = db.views if db is not None else None
settings_collection = db.settings if db is not None else None
withdrawals_collection = db.withdrawals if db is not None else None


def init_default_settings():
    if settings_collection is None:
        return
    
    existing = settings_collection.find_one({'type': 'cpm_rates'})
    if not existing:
        settings_collection.insert_one({
            'type': 'cpm_rates',
            'rates': {
                'US': 5.0,
                'GB': 4.0,
                'IN': 2.0,
                'OTHER': 1.0
            },
            'updated_at': datetime.utcnow()
        })
    
    ad_codes = settings_collection.find_one({'type': 'ad_codes'})
    if not ad_codes:
        settings_collection.insert_one({
            'type': 'ad_codes',
            'codes': {
                'popunder': '',
                'banner': '',
                'native': '',
                'smartlink': '',
                'social_bar': ''
            },
            'updated_at': datetime.utcnow()
        })


def get_or_create_user(user_id: int, username: str = None, referrer_id: int = None) -> Dict:
    if users_collection is None:
        return {}
    
    user = users_collection.find_one({'user_id': user_id})
    if not user:
        user = {
            'user_id': user_id,
            'username': username,
            'balance': 0.0,
            'total_views': 0,
            'files_uploaded': 0,
            'referrer_id': referrer_id,
            'referral_count': 0,
            'referral_earnings': 0.0,
            'created_at': datetime.utcnow()
        }
        users_collection.insert_one(user)
        
        # Award bonus to referrer if exists
        if referrer_id:
            users_collection.update_one(
                {'user_id': referrer_id},
                {
                    '$inc': {
                        'referral_count': 1,
                        'balance': 0.10,  # $0.10 bonus per referral
                        'referral_earnings': 0.10  # Track in referral earnings
                    }
                }
            )
    return user


def update_user_balance(user_id: int, amount: float):
    if users_collection is None:
        return
    
    users_collection.update_one(
        {'user_id': user_id},
        {
            '$inc': {'balance': amount, 'total_views': 1},
            '$set': {'updated_at': datetime.utcnow()}
        }
    )
    
    # Award commission to referrer if exists
    user = users_collection.find_one({'user_id': user_id})
    if user and user.get('referrer_id'):
        award_referral_commission(user['referrer_id'], amount)


def create_file_record(telegram_file_id: str, file_name: str, uploader_id: int, short_link_id: str, short_link: str, file_type: str = 'document') -> Dict:
    if files_collection is None:
        return {}
    
    file_record = {
        'telegram_file_id': telegram_file_id,
        'short_link_id': short_link_id,
        'file_name': file_name,
        'file_type': file_type,
        'uploader_id': uploader_id,
        'short_link': short_link,
        'views': 0,
        'geo_stats': {},
        'created_at': datetime.utcnow()
    }
    files_collection.insert_one(file_record)
    
    users_collection.update_one(
        {'user_id': uploader_id},
        {'$inc': {'files_uploaded': 1}}
    )
    
    return file_record


def get_file_by_short_link_id(short_link_id: str) -> Optional[Dict]:
    if files_collection is None:
        return None
    return files_collection.find_one({'short_link_id': short_link_id})


def increment_file_views(short_link_id: str, country: str):
    if files_collection is None:
        return
    
    files_collection.update_one(
        {'short_link_id': short_link_id},
        {
            '$inc': {
                'views': 1,
                f'geo_stats.{country}': 1
            }
        }
    )


def create_view_record(short_link_id: str, ip: str, country: str, user_agent: str = None):
    if views_collection is None:
        return
    
    view_record = {
        'short_link_id': short_link_id,
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
        'timestamp': datetime.utcnow()
    }
    views_collection.insert_one(view_record)


def check_recent_view(short_link_id: str, ip: str, minutes: int = 5) -> bool:
    if views_collection is None:
        return False
    
    from datetime import timedelta
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    recent_view = views_collection.find_one({
        'short_link_id': short_link_id,
        'ip': ip,
        'timestamp': {'$gte': cutoff_time}
    })
    
    return recent_view is not None


def get_cpm_rates() -> Dict[str, float]:
    if settings_collection is None:
        return {'US': 5.0, 'GB': 4.0, 'IN': 2.0, 'OTHER': 1.0}
    
    settings = settings_collection.find_one({'type': 'cpm_rates'})
    if settings:
        return settings.get('rates', {})
    return {'US': 5.0, 'GB': 4.0, 'IN': 2.0, 'OTHER': 1.0}


def update_cpm_rates(rates: Dict[str, float]):
    if settings_collection is None:
        return
    
    settings_collection.update_one(
        {'type': 'cpm_rates'},
        {
            '$set': {
                'rates': rates,
                'updated_at': datetime.utcnow()
            }
        },
        upsert=True
    )


def get_user_stats(user_id: int) -> Dict:
    if users_collection is None:
        return {}
    
    user = users_collection.find_one({'user_id': user_id})
    if not user:
        return {}
    
    files = list(files_collection.find({'uploader_id': user_id})) if files_collection is not None else []
    
    geo_breakdown = {}
    for file in files:
        for country, count in file.get('geo_stats', {}).items():
            geo_breakdown[country] = geo_breakdown.get(country, 0) + count
    
    return {
        'balance': user.get('balance', 0.0),
        'total_views': user.get('total_views', 0),
        'files_uploaded': user.get('files_uploaded', 0),
        'geo_breakdown': geo_breakdown
    }


def get_all_users_stats() -> List[Dict]:
    if users_collection is None:
        return []
    
    users = list(users_collection.find().sort('balance', -1))
    return users


def calculate_earnings(country: str) -> float:
    rates = get_cpm_rates()
    cpm = rates.get(country, rates.get('OTHER', 1.0))
    return cpm / 1000


def create_withdrawal_request(user_id: int, amount: float, payment_method: str, payment_details: str) -> Dict:
    if withdrawals_collection is None:
        return {}
    
    withdrawal = {
        'user_id': user_id,
        'amount': amount,
        'payment_method': payment_method,
        'payment_details': payment_details,
        'status': 'pending',
        'created_at': datetime.utcnow(),
        'processed_at': None
    }
    result = withdrawals_collection.insert_one(withdrawal)
    withdrawal['_id'] = result.inserted_id
    return withdrawal


def get_user_withdrawals(user_id: int) -> List[Dict]:
    if withdrawals_collection is None:
        return []
    return list(withdrawals_collection.find({'user_id': user_id}).sort('created_at', -1))


def get_pending_withdrawals() -> List[Dict]:
    if withdrawals_collection is None:
        return []
    return list(withdrawals_collection.find({'status': 'pending'}).sort('created_at', 1))


def get_withdrawal_by_id(withdrawal_id):
    if withdrawals_collection is None:
        return None
    
    from bson.objectid import ObjectId
    try:
        return withdrawals_collection.find_one({'_id': ObjectId(withdrawal_id)})
    except:
        return None


def approve_withdrawal(withdrawal_id, admin_note: str = None):
    if withdrawals_collection is None:
        return False
    
    from bson.objectid import ObjectId
    withdrawal = withdrawals_collection.find_one({'_id': ObjectId(withdrawal_id)})
    if not withdrawal:
        return False
    
    users_collection.update_one(
        {'user_id': withdrawal['user_id']},
        {'$inc': {'balance': -withdrawal['amount']}}
    )
    
    withdrawals_collection.update_one(
        {'_id': ObjectId(withdrawal_id)},
        {
            '$set': {
                'status': 'approved',
                'processed_at': datetime.utcnow(),
                'admin_note': admin_note
            }
        }
    )
    return True


def reject_withdrawal(withdrawal_id, admin_note: str = None):
    if withdrawals_collection is None:
        return False
    
    from bson.objectid import ObjectId
    withdrawals_collection.update_one(
        {'_id': ObjectId(withdrawal_id)},
        {
            '$set': {
                'status': 'rejected',
                'processed_at': datetime.utcnow(),
                'admin_note': admin_note
            }
        }
    )
    return True


def get_ad_codes() -> Dict[str, str]:
    if settings_collection is None:
        return {'popunder': '', 'banner': '', 'native': '', 'smartlink': '', 'social_bar': ''}
    
    settings = settings_collection.find_one({'type': 'ad_codes'})
    if settings:
        return settings.get('codes', {})
    return {'popunder': '', 'banner': '', 'native': '', 'smartlink': '', 'social_bar': ''}


def update_ad_code(ad_type: str, code: str):
    if settings_collection is None:
        return False
    
    ad_codes = get_ad_codes()
    ad_codes[ad_type] = code
    
    settings_collection.update_one(
        {'type': 'ad_codes'},
        {
            '$set': {
                'codes': ad_codes,
                'updated_at': datetime.utcnow()
            }
        },
        upsert=True
    )
    return True


def remove_ad_code(ad_type: str):
    if settings_collection is None:
        return False
    
    ad_codes = get_ad_codes()
    ad_codes[ad_type] = ''
    
    settings_collection.update_one(
        {'type': 'ad_codes'},
        {
            '$set': {
                'codes': ad_codes,
                'updated_at': datetime.utcnow()
            }
        },
        upsert=True
    )
    return True


# Referral System Functions
def get_referral_stats(user_id: int) -> Dict:
    """Get referral statistics for a user"""
    if users_collection is None:
        return {}
    
    user = users_collection.find_one({'user_id': user_id})
    if not user:
        return {}
    
    # Get all referred users
    referred_users = list(users_collection.find({'referrer_id': user_id}))
    
    return {
        'referral_count': user.get('referral_count', 0),
        'referral_earnings': user.get('referral_earnings', 0.0),
        'referred_users': [
            {
                'user_id': u['user_id'],
                'username': u.get('username', 'Unknown'),
                'joined_at': u.get('created_at')
            }
            for u in referred_users
        ]
    }


def award_referral_commission(referrer_id: int, amount: float, commission_rate: float = 0.10):
    """Award commission to referrer (10% of referred user's earnings)"""
    if users_collection is None:
        return False
    
    commission = amount * commission_rate
    users_collection.update_one(
        {'user_id': referrer_id},
        {
            '$inc': {
                'balance': commission,
                'referral_earnings': commission
            }
        }
    )
    return True


# File Management Functions
def get_user_files(user_id: int, limit: int = 50, skip: int = 0) -> List[Dict]:
    """Get all files uploaded by a user"""
    if files_collection is None:
        return []
    
    files = list(files_collection.find({'uploader_id': user_id})
                 .sort('created_at', -1)
                 .skip(skip)
                 .limit(limit))
    return files


def get_file_stats(file_id: str) -> Dict:
    """Get detailed statistics for a specific file"""
    if files_collection is None:
        return {}
    
    from bson.objectid import ObjectId
    file_record = files_collection.find_one({'_id': ObjectId(file_id)})
    if not file_record:
        return {}
    
    return {
        'file_name': file_record.get('file_name'),
        'views': file_record.get('views', 0),
        'geo_stats': file_record.get('geo_stats', {}),
        'created_at': file_record.get('created_at'),
        'short_link': file_record.get('short_link')
    }


def delete_file(file_id: str, user_id: int) -> bool:
    """Delete a file (only by owner)"""
    if files_collection is None:
        return False
    
    from bson.objectid import ObjectId
    
    # Verify ownership
    file_record = files_collection.find_one({
        '_id': ObjectId(file_id),
        'uploader_id': user_id
    })
    
    if not file_record:
        return False
    
    # Delete file
    result = files_collection.delete_one({
        '_id': ObjectId(file_id),
        'uploader_id': user_id
    })
    
    if result.deleted_count > 0:
        # Update user's file count
        users_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'files_uploaded': -1}}
        )
        return True
    
    return False


def delete_file_by_short_link(short_link_id: str, user_id: int) -> bool:
    """Delete a file by short link ID (only by owner)"""
    if files_collection is None:
        return False
    
    # Verify ownership
    file_record = files_collection.find_one({
        'short_link_id': short_link_id,
        'uploader_id': user_id
    })
    
    if not file_record:
        return False
    
    # Delete file
    result = files_collection.delete_one({
        'short_link_id': short_link_id,
        'uploader_id': user_id
    })
    
    if result.deleted_count > 0:
        # Update user's file count
        users_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'files_uploaded': -1}}
        )
        return True
    
    return False


def get_file_count(user_id: int) -> int:
    """Get total number of files uploaded by user"""
    if files_collection is None:
        return 0
    
    return files_collection.count_documents({'uploader_id': user_id})


if client is not None:
    init_default_settings()
