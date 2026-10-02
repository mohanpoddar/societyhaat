from fastapi import APIRouter, HTTPException
import json
import re
from pathlib import Path
from datetime import datetime
import uuid

router = APIRouter()
DATA_DIR = Path(__file__).parent.parent / "data"
SEVA_FILE = DATA_DIR / "seva.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"

def load_seva():
    if not SEVA_FILE.exists():
        return []
    try:
        with open(SEVA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('posts', [])
    except Exception as e:
        print(f"load_seva error: {e}")
        return []

def save_seva(data):
    try:
        SEVA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SEVA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"save_seva error: {e}")
        raise

def load_bookings():
    if not BOOKINGS_FILE.exists():
        return []
    try:
        with open(BOOKINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('bookings', [])
    except:
        return []

def save_bookings(data):
    BOOKINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def parse_seats(seats_str):
    if not seats_str:
        return 4
    if 'full' in seats_str.lower():
        return 0
    m = re.search(r'(\d+)', seats_str)
    return int(m.group(1)) if m else 4

@router.get("/list")
async def list_seva(society_id: str = "", type: str = ""):
    posts = load_seva()
    if society_id:
        posts = [p for p in posts if p.get('society_id','sev2').lower() == society_id.lower()]
    if type:
        posts = [p for p in posts if p.get('type','').lower() == type.lower()]
    posts = sorted(posts, key=lambda x: x.get('created_at',''), reverse=True)
    return {"posts": posts, "count": len(posts)}

@router.post("/create")
async def create_seva(payload: dict):
    society_id = payload.get("society_id","sev2").strip() or "sev2"
    type_ = payload.get("type","Help").strip()
    title = payload.get("title","").strip()
    description = payload.get("description","").strip()
    when = payload.get("when","").strip()
    from_to = payload.get("from_to","").strip()
    from_source = payload.get("from_source","").strip()
    to_destination = payload.get("to_destination","").strip()
    date = payload.get("date","").strip()
    time = payload.get("time","").strip()
    seats = payload.get("seats","").strip()
    price = payload.get("price","").strip()
    phone = payload.get("phone","").strip()
    name = payload.get("name","Anonymous").strip()
    flat = payload.get("flat","").strip()
    car = payload.get("car", {})
    car_id = payload.get("car_id","").strip()
    if not title or not description:
        raise HTTPException(status_code=400, detail="Title and description required")
    posts = load_seva()
    seats_total = parse_seats(seats)
    # For Car Pool, ensure at least 1 seat if not full
    if seats_total==0 and 'full' not in seats.lower():
        seats_total = 4
    new_post = {
        "id": str(uuid.uuid4())[:8],
        "society_id": society_id,
        "type": type_,
        "title": title,
        "description": description,
        "when": when,
        "from_to": from_to,
        "from_source": from_source,
        "to_destination": to_destination,
        "date": date,
        "time": time,
        "seats": seats,
        "seats_total": seats_total,
        "seats_booked": 0,
        "seats_pending": 0,
        "seats_left": seats_total,
        "price": price,
        "phone": phone,
        "name": name,
        "flat": flat,
        "car": car,
        "car_id": car_id,
        "bookings": [],
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "owner_closed": False
    }
    posts.append(new_post)
    save_seva(posts)
    return {"message": f"Posted to {society_id.upper()} Seva", "post": new_post}

@router.post("/book")
async def book_ride(payload: dict):
    post_id = payload.get("post_id","").strip()
    booker_phone = payload.get("phone","").strip()
    booker_name = payload.get("name","").strip()
    booker_flat = payload.get("flat","").strip()
    seats_requested = int(payload.get("seats",1))
    if not post_id or not booker_phone:
        raise HTTPException(status_code=400, detail="post_id and phone required")
    if seats_requested <1:
        raise HTTPException(status_code=400, detail="Seats must be >=1")
    posts = load_seva()
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==post_id:
            post = p
            post_idx = i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')==booker_phone:
        raise HTTPException(status_code=400, detail="You cannot book your own ride")
    if post.get('status') in ('full','cancelled') or post.get('owner_closed'):
        raise HTTPException(status_code=400, detail=f"Ride is {post.get('status','full')} - owner closed bookings. Cannot book now")
    pending_booked = sum(b.get('seats_booked',0) for b in post.get('bookings',[]) if b.get('status')=='pending')
    available = post.get('seats_total', post.get('seats_left',0)) - post.get('seats_booked',0) - pending_booked
    if available < seats_requested:
        raise HTTPException(status_code=400, detail=f"Only {available} seats left, you requested {seats_requested}")
    bookings = load_bookings()
    for b in bookings:
        if b.get('post_id')==post_id and b.get('phone')==booker_phone and b.get('status') in ('pending','confirmed'):
            raise HTTPException(status_code=400, detail="You already requested/booked this ride")
    booking = {
        "id": str(uuid.uuid4())[:8],
        "post_id": post_id,
        "ride_owner": post.get('phone'),
        "ride_owner_name": post.get('name'),
        "from_source": post.get('from_source'),
        "to_destination": post.get('to_destination'),
        "date": post.get('date'),
        "time": post.get('time'),
        "phone": booker_phone,
        "name": booker_name,
        "flat": booker_flat,
        "seats_booked": seats_requested,
        "price_per_seat": post.get('price',''),
        "total_price": str(int(post.get('price') or 0) * seats_requested) if post.get('price') else "",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    bookings.append(booking)
    save_bookings(bookings)
    if 'bookings' not in post:
        post['bookings'] = []
    post['bookings'].append(booking)
    post['seats_pending'] = post.get('seats_pending',0) + seats_requested
    posts[post_idx]=post
    save_seva(posts)
    wa_text = f"Hi {post.get('name')} (Seva Saathi), {booker_name} ({booker_flat}) wants to book {seats_requested} seat(s) for your ride {post.get('from_source')} to {post.get('to_destination')} on {post.get('date')} {post.get('time')}. Please Accept/Deny in app. Phone: {booker_phone}"
    return {"message": f"Request sent to {post.get('name')} - pending approval", "booking": booking, "post": post, "whatsapp_text": wa_text}

@router.post("/booking/accept")
async def accept_booking(payload: dict):
    booking_id = payload.get("booking_id","").strip()
    owner_phone = payload.get("owner_phone","").strip()
    if not booking_id or not owner_phone:
        raise HTTPException(status_code=400, detail="booking_id and owner_phone required")
    posts = load_seva()
    bookings = load_bookings()
    booking = None
    booking_idx = -1
    for i,b in enumerate(bookings):
        if b.get('id')==booking_id:
            booking=b
            booking_idx=i
            break
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.get('status')!='pending':
        raise HTTPException(status_code=400, detail=f"Booking not pending, current: {booking.get('status')}")
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==booking.get('post_id'):
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')!=owner_phone:
        raise HTTPException(status_code=403, detail="Only ride owner can accept")
    available = post.get('seats_left',0)
    if available < booking.get('seats_booked',1):
        raise HTTPException(status_code=400, detail=f"Only {available} seats left, cannot accept {booking.get('seats_booked')} seats")
    booking['status']='confirmed'
    booking['confirmed_at']=datetime.now().isoformat()
    bookings[booking_idx]=booking
    save_bookings(bookings)
    for pb in post.get('bookings',[]):
        if pb.get('id')==booking_id:
            pb['status']='confirmed'
            pb['confirmed_at']=booking['confirmed_at']
            break
    post['seats_booked'] = post.get('seats_booked',0) + booking.get('seats_booked',1)
    post['seats_left'] = post.get('seats_total',0) - post.get('seats_booked',0)
    post['seats_pending'] = max(0, post.get('seats_pending',0) - booking.get('seats_booked',1))
    if post['seats_left'] <=0:
        post['seats']='Car full'
        post['status']='full'
    else:
        post['seats']=f"{post['seats_left']} seats"
    posts[post_idx]=post
    save_seva(posts)
    wa_text = f"Hi {booking.get('name')}, your ride {post.get('from_source')} to {post.get('to_destination')} on {post.get('date')} {post.get('time')} ACCEPTED by {post.get('name')} ({post.get('flat')}) ✅ Seva Saathi mobile: {post.get('phone')}. See you! - Society Haat"
    return {"message": f"Accepted {booking.get('name')} - {booking.get('seats_booked')} seat(s)", "booking": booking, "post": post, "whatsapp_text": wa_text}

@router.post("/booking/deny")
async def deny_booking(payload: dict):
    booking_id = payload.get("booking_id","").strip()
    owner_phone = payload.get("owner_phone","").strip()
    reason = payload.get("reason","").strip() or "Seats not available"
    if not booking_id or not owner_phone:
        raise HTTPException(status_code=400, detail="booking_id and owner_phone required")
    posts = load_seva()
    bookings = load_bookings()
    booking = None
    booking_idx = -1
    for i,b in enumerate(bookings):
        if b.get('id')==booking_id:
            booking=b
            booking_idx=i
            break
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.get('status')!='pending':
        raise HTTPException(status_code=400, detail=f"Only pending bookings can be denied, current: {booking.get('status')}")
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==booking.get('post_id'):
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')!=owner_phone:
        raise HTTPException(status_code=403, detail="Only ride owner can deny")
    booking['status']='denied'
    booking['denied_at']=datetime.now().isoformat()
    booking['deny_reason']=reason
    bookings[booking_idx]=booking
    save_bookings(bookings)
    for pb in post.get('bookings',[]):
        if pb.get('id')==booking_id:
            pb['status']='denied'
            pb['denied_at']=booking['denied_at']
            pb['deny_reason']=reason
            break
    post['seats_pending'] = max(0, post.get('seats_pending',0) - booking.get('seats_booked',1))
    posts[post_idx]=post
    save_seva(posts)
    wa_text = f"Hi {booking.get('name')}, your ride {post.get('from_source')} to {post.get('to_destination')} on {post.get('date')} {post.get('time')} was not accepted. Reason: {reason}. Try another ride. - Society Haat"
    return {"message": f"Denied booking of {booking.get('name')}", "booking": booking, "post": post, "whatsapp_text": wa_text}

@router.post("/booking/undo-deny")
async def undo_deny_booking(payload: dict):
    booking_id = payload.get("booking_id","").strip()
    owner_phone = payload.get("owner_phone","").strip()
    if not booking_id or not owner_phone:
        raise HTTPException(status_code=400, detail="booking_id and owner_phone required")
    posts = load_seva()
    bookings = load_bookings()
    booking = None
    booking_idx = -1
    for i,b in enumerate(bookings):
        if b.get('id')==booking_id:
            booking=b
            booking_idx=i
            break
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.get('status') != 'denied':
        raise HTTPException(status_code=400, detail=f"Only denied bookings can be reopened, current: {booking.get('status')}")
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==booking.get('post_id'):
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')!=owner_phone:
        raise HTTPException(status_code=403, detail="Only ride owner can allow again")
    pending_booked = sum(b.get('seats_booked',0) for b in post.get('bookings',[]) if b.get('status')=='pending')
    available = post.get('seats_total', post.get('seats_left',0)) - post.get('seats_booked',0) - pending_booked
    if available < booking.get('seats_booked',1):
        raise HTTPException(status_code=400, detail=f"Only {available} seats left, cannot reopen {booking.get('seats_booked')} seats")
    booking['status']='pending'
    booking['reopened_at']=datetime.now().isoformat()
    booking.pop('denied_at', None)
    booking.pop('deny_reason', None)
    bookings[booking_idx]=booking
    save_bookings(bookings)
    for pb in post.get('bookings',[]):
        if pb.get('id')==booking_id:
            pb['status']='pending'
            pb['reopened_at']=booking['reopened_at']
            pb.pop('denied_at', None)
            pb.pop('deny_reason', None)
            break
    post['seats_pending'] = post.get('seats_pending',0) + booking.get('seats_booked',1)
    posts[post_idx]=post
    save_seva(posts)
    wa_text = f"Hi {booking.get('name')}, good news! Your denied request for {post.get('from_source')} to {post.get('to_destination')} on {post.get('date')} {post.get('time')} has been REOPENED by Seva Saathi {post.get('name')}. Your request is now pending again."
    return {"message": f"Reopened booking of {booking.get('name')} - now pending again", "booking": booking, "post": post, "whatsapp_text": wa_text}

@router.post("/booking/cancel")
async def cancel_my_booking(payload: dict):
    booking_id = payload.get("booking_id","").strip()
    phone = payload.get("phone","").strip()
    reason = payload.get("reason","").strip() or "Changed plan"
    if not booking_id or not phone:
        raise HTTPException(status_code=400, detail="booking_id and phone required")
    posts = load_seva()
    bookings = load_bookings()
    booking = None
    booking_idx = -1
    for i,b in enumerate(bookings):
        if b.get('id')==booking_id:
            booking=b
            booking_idx=i
            break
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.get('phone')!=phone:
        raise HTTPException(status_code=403, detail="Only owner of booking can cancel")
    if booking.get('status') not in ('pending','confirmed'):
        raise HTTPException(status_code=400, detail=f"Cannot cancel {booking.get('status')} booking")
    was_confirmed = booking.get('status')=='confirmed'
    booking['status']='cancelled'
    booking['cancelled_at']=datetime.now().isoformat()
    booking['cancel_reason']=reason
    booking['cancelled_by']='booker'
    bookings[booking_idx]=booking
    save_bookings(bookings)
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==booking.get('post_id'):
            post=p
            post_idx=i
            break
    if post:
        for pb in post.get('bookings',[]):
            if pb.get('id')==booking_id:
                pb['status']='cancelled'
                pb['cancelled_at']=booking['cancelled_at']
                pb['cancel_reason']=reason
                break
        if was_confirmed:
            post['seats_booked'] = max(0, post.get('seats_booked',0) - booking.get('seats_booked',1))
            post['seats_left'] = post.get('seats_total',0) - post.get('seats_booked',0)
            post['seats']=f"{post['seats_left']} seats"
            post['status']='active'
            post['owner_closed']=False
        else:
            post['seats_pending'] = max(0, post.get('seats_pending',0) - booking.get('seats_booked',1))
        posts[post_idx]=post
        save_seva(posts)
    wa_text = f"Hi {post.get('name')}, {booking.get('name')} ({booking.get('flat')}) cancelled booking for {post.get('from_source')} to {post.get('to_destination')} on {post.get('date')} {post.get('time')}. Reason: {reason}. Seat freed: {booking.get('seats_booked')}."
    return {"message": f"Cancelled - {booking.get('seats_booked')} seat(s) freed", "booking": booking, "post": post, "whatsapp_text": wa_text}

@router.post("/booking/owner-cancel")
async def owner_cancel_booking(payload: dict):
    booking_id = payload.get("booking_id","").strip()
    owner_phone = payload.get("owner_phone","").strip()
    reason = payload.get("reason","").strip() or "Sorry, plan changed"
    if not booking_id or not owner_phone:
        raise HTTPException(status_code=400, detail="booking_id and owner_phone required")
    posts = load_seva()
    bookings = load_bookings()
    booking = None
    booking_idx = -1
    for i,b in enumerate(bookings):
        if b.get('id')==booking_id:
            booking=b
            booking_idx=i
            break
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==booking.get('post_id'):
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')!=owner_phone:
        raise HTTPException(status_code=403, detail="Only ride owner can cancel")
    if booking.get('status') not in ('pending','confirmed'):
        raise HTTPException(status_code=400, detail=f"Cannot cancel {booking.get('status')} booking")
    was_confirmed = booking.get('status')=='confirmed'
    booking['status']='cancelled'
    booking['cancelled_at']=datetime.now().isoformat()
    booking['cancel_reason']=reason
    booking['cancelled_by']='owner'
    bookings[booking_idx]=booking
    save_bookings(bookings)
    for pb in post.get('bookings',[]):
        if pb.get('id')==booking_id:
            pb['status']='cancelled'
            pb['cancelled_at']=booking['cancelled_at']
            pb['cancel_reason']=reason
            break
    if was_confirmed:
        post['seats_booked'] = max(0, post.get('seats_booked',0) - booking.get('seats_booked',1))
        post['seats_left'] = post.get('seats_total',0) - post.get('seats_booked',0)
        post['seats']=f"{post['seats_left']} seats"
        post['status']='active'
        post['owner_closed']=False
    else:
        post['seats_pending'] = max(0, post.get('seats_pending',0) - booking.get('seats_booked',1))
    posts[post_idx]=post
    save_seva(posts)
    wa_text = f"Hi {booking.get('name')}, your ride {post.get('from_source')} to {post.get('to_destination')} on {post.get('date')} {post.get('time')} has been CANCELLED by Seva Saathi {post.get('name')} ({post.get('flat')}). Reason: {reason}. Sorry for inconvenience."
    return {"message": f"Cancelled booking of {booking.get('name')} - seat freed", "booking": booking, "post": post, "whatsapp_text": wa_text}

@router.post("/ride/cancel-all")
async def cancel_entire_ride(payload: dict):
    post_id = payload.get("post_id","").strip()
    owner_phone = payload.get("owner_phone","").strip()
    reason = payload.get("reason","").strip() or "I cannot go - emergency. Sorry for inconvenience"
    if not post_id or not owner_phone:
        raise HTTPException(status_code=400, detail="post_id and owner_phone required")
    posts = load_seva()
    bookings = load_bookings()
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==post_id:
            post = p
            post_idx = i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')!=owner_phone:
        raise HTTPException(status_code=403, detail="Only ride owner can cancel ride")
    affected = []
    for b in bookings:
        if b.get('post_id')==post_id and b.get('status') in ('pending','confirmed'):
            b['status']='ride_cancelled'
            b['cancelled_at']=datetime.now().isoformat()
            b['cancel_reason']=reason
            b['cancelled_by']='owner_ride_cancel'
            affected.append(b)
    save_bookings(bookings)
    for pb in post.get('bookings',[]):
        if pb.get('status') in ('pending','confirmed'):
            pb['status']='ride_cancelled'
            pb['cancelled_at']=datetime.now().isoformat()
            pb['cancel_reason']=reason
    post['status']='cancelled'
    post['seats_booked']=0
    post['seats_pending']=0
    post['seats_left']=post.get('seats_total',0)
    post['seats']=f"{post['seats_left']} seats - Ride Cancelled"
    post['cancel_reason']=reason
    post['cancelled_at']=datetime.now().isoformat()
    posts[post_idx]=post
    save_seva(posts)
    whatsapp_list = []
    for b in affected:
        wa_text = f"Hi {b.get('name')} - Your Car Pool ride from {post.get('from_source')} to {post.get('to_destination')} on {post.get('date')} at {post.get('time')} has been CANCELLED by {post.get('name')} ({post.get('flat')}). Reason: {reason}. Apologies."
        whatsapp_list.append({"phone": b.get('phone'), "name": b.get('name'), "text": wa_text})
    return {"message": f"Ride cancelled - {len(affected)} members notified", "post": post, "affected": affected, "whatsapp_list": whatsapp_list, "whatsapp_text": f"Ride {post.get('from_source')} to {post.get('to_destination')} cancelled. {len(affected)} members to notify. Reason: {reason}"}

@router.post("/ride/mark-full")
async def mark_ride_full(payload: dict):
    post_id = payload.get("post_id","").strip() or payload.get("id","").strip()
    owner_phone = payload.get("owner_phone","").strip() or payload.get("phone","").strip()
    reason = payload.get("reason","").strip() or "Marked full by owner - no more seats"
    if not post_id or not owner_phone:
        raise HTTPException(status_code=400, detail="post_id and owner_phone required")
    posts = load_seva()
    bookings = load_bookings()
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==post_id:
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')!=owner_phone:
        raise HTTPException(status_code=403, detail="Only ride owner can mark full")
    if post.get('status')=='full' or post.get('status')=='cancelled':
        raise HTTPException(status_code=400, detail=f"Ride already {post.get('status')}")
    if 'original_seats_left' not in post:
        post['original_seats_left'] = post.get('seats_left', 0)
        post['original_seats_total'] = post.get('seats_total', 0)
    denied_count = 0
    for b in bookings:
        if b.get('post_id')==post_id and b.get('status')=='pending':
            b['status']='denied'
            b['denied_at']=datetime.now().isoformat()
            b['deny_reason']=reason
            b['denied_by']='owner_mark_full'
            denied_count+=1
    save_bookings(bookings)
    for pb in post.get('bookings',[]):
        if pb.get('status')=='pending':
            pb['status']='denied'
            pb['denied_at']=datetime.now().isoformat()
            pb['deny_reason']=reason
    post['status']='full'
    post['seats_left']=0
    post['seats']='Car full - Closed by owner'
    post['owner_closed']=True
    post['closed_at']=datetime.now().isoformat()
    post['close_reason']=reason
    post['seats_pending']=0
    posts[post_idx]=post
    save_seva(posts)
    wa_text = f"Ride {post.get('from_source')} to {post.get('to_destination')} marked FULL by owner. {denied_count} pending denied. {post.get('seats_booked',0)} confirmed still going."
    return {"message": f"Marked as FULL - {post.get('seats_booked',0)} confirmed, {denied_count} pending denied", "post": post, "denied_count": denied_count, "whatsapp_text": wa_text}

@router.post("/ride/mark-open")
async def mark_ride_open(payload: dict):
    post_id = payload.get("post_id","").strip() or payload.get("id","").strip()
    owner_phone = payload.get("owner_phone","").strip() or payload.get("phone","").strip()
    if not post_id or not owner_phone:
        raise HTTPException(status_code=400, detail="post_id and owner_phone required")
    posts = load_seva()
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==post_id:
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    if post.get('phone')!=owner_phone:
        raise HTTPException(status_code=403, detail="Only ride owner can reopen")
    if post.get('status')!='full':
        raise HTTPException(status_code=400, detail=f"Ride not full, current: {post.get('status')}")
    original_left = post.get('original_seats_left', post.get('seats_total',4) - post.get('seats_booked',0))
    post['seats_left']=original_left
    post['status']='active'
    post['seats']=f"{original_left} seats"
    post['owner_closed']=False
    post.pop('closed_at', None)
    post.pop('close_reason', None)
    posts[post_idx]=post
    save_seva(posts)
    return {"message": f"Ride reopened - {original_left} seats available again", "post": post}

@router.post("/booking/add-seats")
async def add_seats_to_booking(payload: dict):
    booking_id = payload.get("booking_id","").strip()
    post_id = payload.get("post_id","").strip()
    phone = payload.get("phone","").strip()
    additional_seats = int(payload.get("additional_seats", 1))
    if not phone:
        raise HTTPException(status_code=400, detail="Phone required")
    if additional_seats < 1:
        raise HTTPException(status_code=400, detail="Additional seats must be >=1")
    posts = load_seva()
    bookings = load_bookings()
    booking = None
    booking_idx = -1
    if booking_id:
        for i,b in enumerate(bookings):
            if b.get('id')==booking_id:
                booking=b
                booking_idx=i
                break
    elif post_id:
        for i,b in enumerate(bookings):
            if b.get('post_id')==post_id and b.get('phone')==phone and b.get('status')=='confirmed':
                booking=b
                booking_idx=i
                break
    if not booking:
        raise HTTPException(status_code=404, detail="Confirmed booking not found - book first")
    if booking.get('phone')!=phone:
        raise HTTPException(status_code=403, detail="Only owner of booking can add seats")
    if booking.get('status')!='confirmed':
        raise HTTPException(status_code=400, detail=f"Only confirmed bookings can add seats, current: {booking.get('status')}")
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==booking.get('post_id'):
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Ride not found")
    available = post.get('seats_left', 0)
    if available < additional_seats:
        raise HTTPException(status_code=400, detail=f"Only {available} seats left, you requested {additional_seats} more")
    booking['seats_booked'] = booking.get('seats_booked',1) + additional_seats
    if booking.get('total_price'):
        try:
            price_per = int(booking.get('price_per_seat') or post.get('price') or 0)
            booking['total_price'] = str(price_per * booking['seats_booked'])
        except:
            pass
    booking['updated_at'] = datetime.now().isoformat()
    bookings[booking_idx]=booking
    save_bookings(bookings)
    for pb in post.get('bookings',[]):
        if pb.get('id')==booking.get('id'):
            pb['seats_booked']=booking['seats_booked']
            if pb.get('total_price') is not None:
                pb['total_price']=booking.get('total_price','')
            break
    post['seats_booked'] = post.get('seats_booked',0) + additional_seats
    post['seats_left'] = post.get('seats_total',0) - post.get('seats_booked',0)
    if post['seats_left'] <=0:
        post['seats']='Car full'
        post['status']='full'
    else:
        post['seats']=f"{post['seats_left']} seats"
    posts[post_idx]=post
    save_seva(posts)
    wa_text = f"Hi {post.get('name')} (Seva Saathi), {booking.get('name')} ({booking.get('flat')}) added {additional_seats} more seat(s). Now total {booking['seats_booked']} seat(s) booked. You have {post['seats_left']} seats left. Thanks!"
    return {"message": f"Added {additional_seats} seat(s). Now total {booking['seats_booked']}", "booking": booking, "post": post, "whatsapp_text": wa_text}

@router.get("/bookings")
async def get_bookings(phone: str = "", post_id: str = ""):
    bookings = load_bookings()
    if phone:
        bookings = [b for b in bookings if b.get('phone')==phone or b.get('ride_owner')==phone]
    if post_id:
        bookings = [b for b in bookings if b.get('post_id')==post_id]
    bookings = sorted(bookings, key=lambda x: x.get('created_at',''), reverse=True)
    return {"bookings": bookings, "count": len(bookings)}


@router.post("/update")
async def update_seva(payload: dict):
    """Mohan edits his seva/ride after posting - add fee, change time, etc"""
    post_id = payload.get("id","").strip() or payload.get("post_id","").strip()
    phone = payload.get("phone","").strip() or payload.get("owner_phone","").strip()
    if not post_id or not phone:
        raise HTTPException(status_code=400, detail="id/post_id and phone required")
    posts = load_seva()
    post = None
    post_idx = -1
    for i,p in enumerate(posts):
        if p.get('id')==post_id:
            post=p
            post_idx=i
            break
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.get('phone') != phone:
        raise HTTPException(status_code=403, detail="Only owner can edit ride")
    # Check if cancelled
    if post.get('status')=='cancelled':
        raise HTTPException(status_code=400, detail="Cannot edit cancelled ride")
    
    # Fields that can be updated
    # For car pool: title, description, price, date, time, from_source, to_destination, seats (if no bookings), car, car_id
    # For general seva: title, description, type, from_to, when
    
    # Prevent reducing seats below already booked
    new_seats_str = payload.get("seats","").strip()
    if new_seats_str:
        new_total = parse_seats(new_seats_str)
        booked = post.get('seats_booked',0)
        if new_total < booked and new_total!=0:
            raise HTTPException(status_code=400, detail=f"Cannot reduce seats to {new_total} - already {booked} booked. Increase or keep same.")
        # Update seats_total and seats_left
        post['seats'] = new_seats_str
        post['seats_total'] = new_total if new_total!=0 else post.get('seats_total',0)
        # Recalc left
        if post.get('status')!='full' and not post.get('owner_closed'):
            post['seats_left'] = max(0, post['seats_total'] - post.get('seats_booked',0))
            if post['seats_left']<=0 and post['seats_total']>0:
                post['status']='full'
                post['seats']='Car full'
    
    if "title" in payload and payload["title"].strip():
        post['title'] = payload["title"].strip()
    if "description" in payload and payload["description"].strip():
        post['description'] = payload["description"].strip()
    if "price" in payload:
        # Price can be updated anytime - important for Mohan's fee case
        post['price'] = str(payload["price"]).strip()
        # Also update bookings price per seat for pending bookings
        # (confirmed bookings keep old price, but we update display)
    if "date" in payload and payload["date"].strip():
        post['date'] = payload["date"].strip()
    if "time" in payload and payload["time"].strip():
        post['time'] = payload["time"].strip()
    if "from_source" in payload and payload["from_source"].strip():
        post['from_source'] = payload["from_source"].strip()
    if "to_destination" in payload and payload["to_destination"].strip():
        post['to_destination'] = payload["to_destination"].strip()
    if "from_to" in payload and payload["from_to"].strip():
        post['from_to'] = payload["from_to"].strip()
    if "when" in payload and payload["when"].strip():
        post['when'] = payload["when"].strip()
    if "car" in payload and payload["car"]:
        post['car'] = payload["car"]
    if "car_id" in payload and payload["car_id"].strip():
        post['car_id'] = payload["car_id"].strip()
    if "type" in payload and payload["type"].strip():
        post['type'] = payload["type"].strip()
    
    post['updated_at'] = datetime.now().isoformat()
    post['edited'] = True
    
    posts[post_idx]=post
    save_seva(posts)
    
    # If price changed, update pending bookings total_price
    if "price" in payload:
        try:
            bookings = load_bookings()
            price_per = int(post.get('price') or 0)
            for b in bookings:
                if b.get('post_id')==post_id and b.get('status')=='pending':
                    b['price_per_seat'] = post.get('price','')
                    b['total_price'] = str(price_per * b.get('seats_booked',1)) if price_per else ""
            save_bookings(bookings)
            # Also update post.bookings
            for pb in post.get('bookings',[]):
                if pb.get('status')=='pending':
                    pb['price_per_seat']=post.get('price','')
                    pb['total_price']=str(price_per * pb.get('seats_booked',1)) if price_per else ""
        except:
            pass
    
    return {"message": "Ride updated successfully - fee/time/location changed", "post": post}


@router.post("/delete")
async def delete_seva(payload: dict):
    post_id = payload.get("id","").strip() or payload.get("post_id","").strip()
    phone = payload.get("phone","").strip() or payload.get("owner_phone","").strip()
    force = payload.get("force", False)
    if not post_id:
        raise HTTPException(status_code=400, detail="id/post_id required")
    posts = load_seva()
    post = None
    for i,p in enumerate(posts):
        if p.get('id')==post_id:
            post=p
            break
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if phone and post.get('phone') != phone:
        raise HTTPException(status_code=403, detail="Only owner can delete ride")
    active = [b for b in post.get('bookings',[]) if b.get('status') in ('pending','confirmed')]
    if active and not force:
        raise HTTPException(status_code=400, detail=f"Cannot delete: {len(active)} active booking(s) - cancel all bookings first")
    remaining = [p for p in posts if p.get('id') != post_id]
    save_seva(remaining)
    bookings = load_bookings()
    for b in bookings:
        if b.get('post_id')==post_id and b.get('status') in ('pending','confirmed','denied'):
            b['status']='ride_deleted'
            b['deleted_at']=datetime.now().isoformat()
    save_bookings(bookings)
    return {"message": "Ride deleted successfully", "deleted_id": post_id}
