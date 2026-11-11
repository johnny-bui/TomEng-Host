#!/usr/bin/env python3
"""Build the independent TomEng Host catalog from the stable TomEng core.

Every Host scenario contains five linked turns and owns five candidate IDs.
The 625 Everyday/Reflex phrase records are retained by ID; 575 former
workplace IDs are assigned to apartment-operation content in this repository.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
HOST = CONTENT / "host"
CORE = HOST / "tomeng-common-core.json"
read = lambda path: json.loads(path.read_text(encoding="utf-8"))
write = lambda path, data: path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

CORE_DATA = read(CORE)
CORE_PHRASES = CORE_DATA["phrases"]
CORE_LESSONS = CORE_DATA["lessons"]
CORE_PATTERNS = CORE_DATA["patterns"]
CORE_CATEGORIES = CORE_DATA["categories"]
CORE_SUBCATEGORIES = CORE_DATA["subcategories"]
CORE_BY_ID = {phrase["id"]: phrase for phrase in CORE_PHRASES}
COMMON_CATEGORIES = {"everyday", "reflex"}

CATEGORY_DATA = [
    {"id":"rooms","name":"Phòng, giá & tình trạng trống","description":"Tư vấn loại phòng, tiện nghi, giá theo đêm hoặc tháng và lịch xem phòng.","icon":"book","register":"guest-facing friendly-professional","flow_names":["Tìm phòng và kiểm tra ngày","So sánh giá và loại phòng","Xác nhận tiện nghi và xem phòng"],"cases":[
        ("Tìm studio theo tuần","a furnished studio for a week","weekly cleaning and a kitchenette","a one-bedroom with more storage"),
        ("Báo phòng một phòng ngủ","a one-bedroom near the elevator","a quiet courtyard view","a studio on a higher floor"),
        ("Tư vấn lưu trú theo tháng","a monthly stay near the clinic","a monthly rate with weekly cleaning","a shorter weekly booking"),
        ("Tìm phòng yên tĩnh","a quiet room facing the courtyard","a room away from the street","a room on the upper floor"),
        ("Tìm phòng có bếp nhỏ","a studio with a kitchenette","a fridge and a two-burner cooktop","a larger one-bedroom"),
        ("Hỏi phòng dễ tiếp cận","an accessible room on a lower floor","step-free access from the lobby","a unit closer to the elevator"),
        ("Tìm chỗ làm việc trong phòng","a room with a desk for remote work","a desk, a chair, and reliable Wi-Fi","a co-working lounge downstairs"),
        ("Báo phòng cho một người ở dài hạn","a long-term studio for one guest","a monthly rate with utilities listed separately","a furnished one-bedroom"),
        ("Tìm phòng cho gia đình nhỏ","a room for three guests","an extra bed and a family seating area","two adjoining studios"),
        ("Hỏi phòng có ban công","a studio with a balcony","a furnished unit with an open view","a room with a larger living area"),
        ("Kiểm tra phòng cho khách có thú cưng","a pet-friendly unit","the building's pet policy and cleaning fee","a nearby unit with easier outdoor access"),
        ("Tìm chỗ ở gần khu văn phòng","a weekly stay near the business district","a desk and a short commute","a monthly booking at a lower nightly rate"),
    ]},
    {"id":"booking","name":"Đặt phòng & xác nhận","description":"Tiếp nhận yêu cầu, xác nhận chi tiết, thay đổi lịch và gửi hướng dẫn trước chuyến đi.","icon":"bookmark","register":"guest-facing friendly-professional","flow_names":["Xác nhận đặt phòng","Đổi ngày hoặc chi tiết","Ghi nhận yêu cầu đặc biệt"],"cases":[
        ("Xác nhận booking cuối tuần","a weekend booking","the guest's name and arrival date","the confirmation email"),
        ("Gửi mã xác nhận","a reservation under the guest's name","a booking reference for the guest","a copy of the confirmation"),
        ("Đổi ngày đến","a change to the arrival date","the new dates before changing the reservation","the updated booking details"),
        ("Đổi ngày trả phòng","a later check-out date","availability for the extra night","the revised total"),
        ("Thêm khách vào booking","an additional guest on the reservation","the guest count and room capacity","the updated guest details"),
        ("Ghi nhận yêu cầu giường phụ","a request for an extra bed","whether the room can fit the extra bed","the additional charge"),
        ("Gửi chính sách hủy","the cancellation terms","the free-cancellation deadline","a link to the full policy"),
        ("Xác nhận khách đến muộn","a late arrival after midnight","the expected arrival time","the after-hours entry instructions"),
        ("Xử lý khách chưa nhận email","a confirmation email that has not arrived","the email address used for the booking","a fresh copy of the confirmation"),
        ("Ghi nhận yêu cầu tầng cao","a request for a higher floor","which floors are available","a note on the reservation"),
        ("Gửi hướng dẫn trước ngày đến","the arrival instructions","the best contact number for the guest","the check-in guide by message"),
        ("Sửa thông tin người nhận hóa đơn","a change to the billing name","the correct name and company details","an updated invoice after check-out"),
    ]},
    {"id":"checkin","name":"Đến nơi, check-in & check-out","description":"Hướng dẫn vào tòa nhà, nhận chìa khóa, Wi-Fi, giờ nhận và trả phòng.","icon":"home","register":"guest-facing friendly-professional","flow_names":["Hướng dẫn vào phòng","Đến sớm hoặc muộn","Trả phòng gọn gàng"],"cases":[
        ("Hướng dẫn từ sảnh lên phòng","the lobby to unit 204","the lift beside the reception desk","the key card at the front desk"),
        ("Gửi mã cửa chính","the main entrance after hours","the keypad beside the glass door","the private entry code"),
        ("Tìm đúng tầng và căn hộ","unit 305 on the third floor","the lift near the courtyard","the unit number on the door"),
        ("Khách đến trước giờ nhận phòng","an arrival before check-in time","whether the room is ready yet","the luggage room in the lobby"),
        ("Khách đến sau nửa đêm","an arrival after midnight","the self check-in steps","the on-call contact number"),
        ("Hỏi mật khẩu Wi-Fi","the Wi-Fi details for the room","the network name on the welcome card","the password printed by the desk"),
        ("Khách cần hỗ trợ hành lý","help with two large suitcases","the guest's arrival time","a staff member at the entrance"),
        ("Khách muốn gửi hành lý sớm","early luggage drop-off","the time the luggage room opens","a secure spot near reception"),
        ("Gia hạn trả phòng thêm một giờ","a one-hour late check-out","whether the next booking allows it","a confirmed time by message"),
        ("Nhắc giờ trả phòng","check-out at 11 a.m.","the key drop box by reception","a final room check"),
        ("Khách làm mất thẻ phòng","a missing key card for unit 408","when the card was last seen","a replacement card at reception"),
        ("Giải thích đường vào bãi xe","the parking entrance on Pine Street","the visitor spaces on level B1","the lift from the parking area"),
    ]},
    {"id":"housekeeping","name":"Dọn phòng & đồ dùng","description":"Đổi lịch dọn, bổ sung khăn ga, giặt ủi và xử lý yêu cầu trong phòng.","icon":"spark","register":"guest-facing friendly-professional","flow_names":["Sắp lịch dọn phòng","Bổ sung đồ dùng","Giặt ủi và đồ vải"],"cases":[
        ("Đổi giờ dọn phòng","housekeeping at 2 p.m.","the room while the guest is out","a morning visit"),
        ("Xin thêm khăn tắm","two extra bath towels","the towels before 6 p.m.","a fresh set from the linen closet"),
        ("Bổ sung giấy vệ sinh","an extra pack of toilet paper","the supplies to the room","a delivery within the hour"),
        ("Xin thêm chăn","an extra blanket for the room","a blanket from housekeeping","a warmer duvet if available"),
        ("Đổi ga giường","fresh bed linen today","the linen change before the afternoon","a time that suits the guest"),
        ("Khách không muốn dọn hôm nay","skipping today's room cleaning","the do-not-disturb sign on the door","a new cleaning time tomorrow"),
        ("Xin dọn nhanh trước cuộc gọi","a quick tidy before a video call","the room between 1 and 2 p.m.","a fresh towel delivery first"),
        ("Hỏi lịch giặt ủi","laundry pickup this afternoon","the collection bag by the door","the next morning's delivery"),
        ("Báo thiếu đồ dùng","a missing set of hangers","the item to the room","a replacement from storage"),
        ("Xin thêm gối","two firmer pillows","the pillows before bedtime","a softer set if those are unavailable"),
        ("Sắp lịch dọn cho khách dài hạn","weekly cleaning on Thursdays","the room while the guest is at work","a different day each week"),
    ]},
    {"id":"maintenance","name":"Bảo trì & sự cố kỹ thuật","description":"Tiếp nhận lỗi máy lạnh, nước nóng, điện, Internet, khóa và điều phối kỹ thuật viên.","icon":"settings","register":"guest-facing friendly-professional","flow_names":["Tiếp nhận và kiểm tra lỗi","Hẹn kỹ thuật viên","Sự cố cần xử lý ngay"],"cases":[
        ("Máy lạnh không mát","the air conditioner in unit 204","whether the fan is running","a technician to check it this afternoon"),
        ("Nước nóng không hoạt động","the water heater in the bathroom","when the hot water stopped","a maintenance visit before 7 p.m."),
        ("Wi-Fi chập chờn","the Wi-Fi in unit 305","whether other devices are affected","a router reset and a technician check"),
        ("Ổ điện không hoạt động","the outlet beside the desk","whether the breaker has tripped","an electrician to inspect it"),
        ("Khóa cửa khó mở","the lock on the room door","whether the spare key works","a locksmith to come by"),
        ("Vòi nước bị rò","a leaking faucet under the sink","how quickly the water is spreading","a plumber with a replacement seal"),
        ("Thang máy dừng ở một tầng","the elevator between floors","whether anyone is inside","building security to check it now"),
        ("Tủ lạnh không lạnh","the fridge in the kitchenette","whether the door seals properly","a replacement fridge if needed"),
        ("Đèn phòng tắm bị hỏng","the bathroom light","whether the backup light works","a maintenance visit tomorrow morning"),
        ("Máy giặt không xả nước","the washer in the laundry room","whether the filter is clear","a technician to inspect the drain"),
        ("Mất điện trong căn hộ","the power outage in the unit","whether the hallway lights are on","building maintenance to check the circuit"),
        ("Báo khói kêu liên tục","the smoke alarm in the hallway","whether there is smoke or a burning smell","the building guard to inspect it immediately"),
    ]},
    {"id":"complaints","name":"Phản hồi & giải quyết phàn nàn","description":"Lắng nghe, xin lỗi phù hợp, hỏi chi tiết, đưa phương án và hẹn cập nhật.","icon":"lifebuoy","register":"guest-facing empathetic-professional","flow_names":["Lắng nghe và xin lỗi","Đưa phương án phù hợp","Cập nhật đến khi xử lý xong"],"cases":[
        ("Phòng chưa được dọn sạch","the room not being properly cleaned","which areas still need attention","a housekeeping team to return within 30 minutes"),
        ("Tiếng ồn vào buổi tối","noise from the next unit","when the noise started","building security to speak with the neighbor"),
        ("Phòng khác với ảnh đăng","the room looking different from the listing","which part does not match the photos","a move to another available unit"),
        ("Phí chưa rõ trên hóa đơn","an unexpected cleaning charge","which line item looks incorrect","a corrected statement after review"),
        ("Khăn có vết bẩn","a stained towel in the bathroom","how many towels need replacing","fresh towels delivered right away"),
        ("Mùi lạ trong phòng","an unusual smell in the room","when the smell is strongest","a room check and an air purifier"),
        ("Wi-Fi chậm khi họp","slow Wi-Fi during a work call","whether the connection dropped completely","a backup hotspot while we check the router"),
        ("Khách phải chờ check-in","a long wait at check-in","when the guest arrived","a quick room update and a drink in the lounge"),
        ("Thiếu vật dụng trong bếp","missing kitchen items","which items are not in the room","a replacement set delivered today"),
        ("Điều hòa quá ồn","a noisy air conditioner","whether the noise happens all night","a technician check or a quieter room"),
        ("Nước nóng không ổn định","the hot water turning cold","how long the issue has been happening","a maintenance visit and an update by 5 p.m."),
        ("Yêu cầu hoàn tiền một khoản phí","a charge the guest would like reviewed","the booking date and receipt","the manager to review it by tomorrow"),
    ]},
    {"id":"billing","name":"Tiền thuê, đặt cọc & hóa đơn","description":"Trao đổi tiền phòng, phương thức thanh toán, biên nhận, gia hạn và khoản cọc.","icon":"copy","register":"guest-facing clear-professional","flow_names":["Nhắc khoản đến hạn","Gửi hóa đơn và biên nhận","Gia hạn hoặc hoàn cọc"],"cases":[
        ("Nhắc tiền thuê tháng","the monthly rent for unit 204","the payment due date on the invoice","a receipt as soon as payment clears"),
        ("Khách hỏi cách thanh toán","the payment options for the booking","whether bank transfer or card is preferred","a secure payment link"),
        ("Gửi hóa đơn công ty","an invoice under the company name","the billing name and tax details","a revised invoice by email"),
        ("Xác nhận đã nhận tiền cọc","the security deposit for unit 305","the transfer reference","a deposit receipt today"),
        ("Hỏi thời gian hoàn cọc","the deposit refund after check-out","whether there are any outstanding charges","an update after the room inspection"),
        ("Gia hạn hợp đồng thêm một tháng","a one-month extension","availability after the current end date","the revised monthly rate"),
        ("Tính phí ở thêm một đêm","one extra night after Friday","the room's availability and nightly rate","the updated total before confirming"),
        ("Chia hóa đơn theo kỳ","the rent split across two invoices","the dates for each billing period","both invoices by the end of the day"),
        ("Khách báo đã chuyển khoản","a bank transfer made this morning","the transfer receipt","a confirmation once it appears in our account"),
        ("Điều chỉnh ngày thanh toán","moving the monthly payment date","which date works better","the change in writing before the next cycle"),
        ("Tổng kết chi phí khi trả phòng","the final statement for the stay","the room charges and any extras","an itemized copy by email"),
    ]},
    {"id":"safety","name":"An toàn & nội quy tòa nhà","description":"Xử lý mất chìa khóa, tiếng ồn, khách thăm, an toàn khẩn cấp và quy định chung.","icon":"shield","register":"guest-facing calm-professional","flow_names":["Báo bảo vệ hoặc xử lý tiếng ồn","Hỗ trợ mất chìa khóa và khách thăm","Hướng dẫn khi khẩn cấp"],"cases":[
        ("Báo tiếng ồn sau giờ yên tĩnh","noise after quiet hours","when it started and which floor it is on","the building guard to check the hallway"),
        ("Khách thăm chưa đăng ký","a visitor who has not checked in","the visitor's name and unit number","the front desk to register them"),
        ("Mất chìa khóa ngoài giờ","a lost key after reception closes","whether the guest is safely inside","the on-call staff member with a spare"),
        ("Không mở được cổng chính","the main gate not opening","whether the keypad lights up","security to meet the guest at the entrance"),
        ("Khách hỏi quy định hút thuốc","the building's smoking rules","which outdoor areas are permitted","the floor plan with designated areas"),
        ("Khách để quên đồ ở sảnh","a bag left in the lobby","when the guest last saw it","the security desk to check the lost-property log"),
        ("Ngửi thấy mùi khét","a burning smell near the kitchen","whether there is visible smoke","the building guard and emergency services if needed"),
        ("Báo nước tràn ra hành lang","water spreading into the hallway","whether anyone is near the wet area","maintenance to shut off the water supply"),
        ("Khách thấy người lạ ở tầng","an unfamiliar person on the floor","where they are now","building security to check the corridor"),
        ("Hỏi quy định khu vực hồ bơi","the pool opening hours and safety rules","whether children will be using the pool","the posted pool guidelines"),
        ("Mất điện khu vực chung","a power cut in the common area","whether the emergency lights are on","the building team to inspect the backup system"),
    ]},
    {"id":"team","name":"Phối hợp nhân viên & nhà cung cấp","description":"Giao việc rõ ràng cho lễ tân, buồng phòng, bảo vệ, kỹ thuật và nhà cung cấp.","icon":"users","register":"team-internal concise-professional","flow_names":["Phân công và xác nhận việc","Điều phối kỹ thuật viên","Bàn giao ca và cập nhật"],"cases":[
        ("Giao ca dọn phòng","the turnover clean in unit 204","before the next guest arrives at 3 p.m.","a photo when the room is ready"),
        ("Nhờ kiểm tra phòng trống","the vacant room on level four","the lights, air conditioning, and bathroom","the room status in the shift log"),
        ("Điều phối giao khăn ga","the linen delivery for this afternoon","the clean sets for floors two and three","a count before the driver leaves"),
        ("Báo bảo vệ hỗ trợ khách đến","a guest arriving at the north entrance","around 10:30 p.m.","a message when the guest is inside"),
        ("Hẹn thợ kiểm tra khóa","the locksmith visit for unit 305","between 1 and 2 p.m.","confirmation that the spare key works"),
        ("Nhờ kỹ thuật kiểm tra điều hòa","the air-conditioner inspection","before the guest returns at 6 p.m.","a short note on the repair"),
        ("Giao việc bổ sung đồ phòng","the amenity restock in unit 408","before the afternoon check-in","a tick on the restock checklist"),
        ("Xác nhận nhà cung cấp giao hàng","the replacement fridge delivery","at the service entrance","the delivery slip and installation time"),
        ("Bàn giao yêu cầu còn dang dở","the guest request for a late check-out","before the morning shift ends","a direct handoff to reception"),
        ("Chốt danh sách phòng cần kiểm tra","the rooms marked for inspection","before the weekend arrivals","an update in the shared log"),
        ("Nhờ nhân viên xác nhận vật thất lạc","the phone found in the lounge","with the front desk before noon","a call to the guest after verification"),
    ]},
    {"id":"messaging","name":"Tin nhắn, điện thoại & hiếu khách","description":"Trả lời nhanh qua chat, gọi lại, chia sẻ chỉ dẫn và trò chuyện thân thiện với khách.","icon":"message","register":"guest-facing warm-professional","flow_names":["Trả lời cuộc gọi","Nhắn cập nhật ngắn gọn","Chào hỏi và hỏi thăm"],"cases":[
        ("Trả lời khách hỏi giờ đến","your arrival time","whether check-in is available before 2 p.m.","an update when the room is ready"),
        ("Gọi lại khách nhỡ cuộc gọi","a missed call about the reservation","a good time to call back","the answer by message if they prefer"),
        ("Nhắn địa chỉ cho tài xế","directions to the building","the north entrance on Pine Street","a map pin by chat"),
        ("Cập nhật phòng đang được chuẩn bị","the room preparation status","the latest check from housekeeping","a message as soon as the room is ready"),
        ("Báo quán ăn gần căn hộ","a nearby place for dinner","whether the guest prefers local or vegetarian food","two options with directions"),
        ("Trả lời khách hỏi gửi đồ","luggage storage before check-in","the expected arrival time","the storage location in the lobby"),
        ("Nhắn xác nhận đã nhận yêu cầu","the extra pillow request","the delivery window this evening","a note when it has been delivered"),
        ("Xin lỗi vì phản hồi chậm","the delayed reply to the guest's message","whether the issue is still happening","a direct update before the end of the hour"),
        ("Hỏi thăm khách sau đêm đầu","the guest's first night in the apartment","whether everything in the room is working","help with anything they need today"),
        ("Chúc khách chuyến đi vui vẻ","the guest's departure tomorrow","whether they need a taxi","a car pickup at the front entrance"),
        ("Xác nhận đã gửi hướng dẫn","the check-in guide by WhatsApp","whether the link opens on their phone","a copy by email as well"),
    ]},
]

# Select the dialogue template by the actual case intent instead of blindly
# rotating through five-question flows. This keeps a linen request out of the
# cleaning schedule dialogue and keeps urgent hazards in the safety flow.
FLOW_ASSIGNMENTS = {
    'rooms':[0,0,1,0,2,2,2,1,0,2,1,0],
    'booking':[0,0,1,1,1,2,2,2,0,2,0,1],
    'checkin':[0,0,0,1,1,0,1,1,2,2,1,0],
    'housekeeping':[0,1,1,1,1,0,0,2,1,1,0],
    'maintenance':[0,1,0,2,1,2,2,0,0,0,2,2],
    'complaints':[0,0,1,1,0,0,1,1,0,1,1,2],
    'billing':[0,0,2,0,2,2,0,1,0,2,1],
    'safety':[0,1,1,0,1,1,2,2,0,1,2],
    'team':[0,0,1,0,1,1,0,1,2,0,2],
    'messaging':[0,0,1,1,2,0,1,1,2,0,2,1],
}

FLOW_TEMPLATES = {
"rooms":[
 [
  ("Thanks for asking about {topic}.","Cảm ơn bạn đã hỏi về {topic}.","acknowledge","“Thanks for asking about…” mở đầu thân thiện rồi nêu đúng loại phòng khách quan tâm."),
  ("What dates should I check for {topic}?","Bạn muốn tôi kiểm tra ngày nào cho {topic}?","clarify-dates","Hỏi ngày trước khi xác nhận phòng trống hoặc báo giá."),
  ("I’ll check availability for {dates}.","Tôi sẽ kiểm tra phòng trống từ {dates}.","check-availability","“check availability for + dates” cho biết bạn đang kiểm tra đúng khoảng ngày."),
  ("We can offer the {unit} at {rate}; it includes {detail}.","Bên tôi có thể bố trí {unit} với giá {rate}, đã bao gồm {detail}.","offer-rate","Dùng “at + rate” để báo giá và “includes” để nói rõ tiện nghi đi kèm."),
  ("Would you like me to send a quote for the {unit}?","Bạn có muốn tôi gửi báo giá cho {unit} không?","confirm-next-step","“Would you like me to…?” đưa ra bước tiếp theo mà không gây áp lực."),
 ],
 [
  ("How long are you planning to stay in the {unit}?","Bạn dự định lưu trú trong bao lâu?","ask-duration","Hỏi thời lượng trước khi đề xuất giá theo tuần hay theo tháng."),
  ("For {duration}, the {unit} may be the better fit.","Với thời gian {duration}, căn hộ này có thể phù hợp hơn.","match-option","“For + thời lượng” nối nhu cầu khách với lựa chọn phù hợp."),
  ("The rate is {rate} and covers {detail}.","Giá là {rate} và bao gồm {detail}.","explain-rate","“covers” giới thiệu khoản đã bao gồm; nói cụ thể để tránh hiểu nhầm."),
  ("If you need {priority}, we also have {alternative}.","Nếu bạn có ưu tiên riêng, bên tôi cũng có phương án khác.","offer-alternative","“If you need…” giới thiệu phương án khác dựa trên ưu tiên khách."),
  ("I can send both rates for the {unit} and {alternative} so you can compare.","Tôi có thể gửi cả hai mức giá để bạn so sánh.","offer-comparison","“both options” gom hai lựa chọn vừa nêu vào cùng bước so sánh."),
 ],
 [
  ("Are you looking for {priority} in the room?","Bạn đang tìm tiện nghi nào trong phòng?","clarify-preference","Hỏi một tiêu chí cụ thể trước khi tư vấn tiện nghi."),
  ("The {unit} comes with {detail}.","{unit} có {detail}.","describe-inclusion","“comes with” giới thiệu tiện nghi đi kèm tự nhiên trong hội thoại tư vấn."),
  ("We can show you {alternative} as well.","Bên tôi cũng có thể giới thiệu {alternative}.","compare-room","“as well” thêm lựa chọn thứ hai mà không phủ nhận lựa chọn đầu."),
  ("A viewing of the {unit} takes about 15 minutes.","Buổi xem phòng mất khoảng 15 phút.","set-expectation","Dùng “takes about” để báo thời lượng ước tính."),
  ("Would {time} work for you?","{time} có thuận tiện cho bạn không?","confirm-time","“Would … work for you?” là cách chốt giờ lịch sự."),
 ]
],
"booking":[
 [
  ("I have your booking for {dates} under {guest}.","Tôi thấy đặt phòng từ {dates} dưới tên {guest}.","locate-booking","Đặt khoảng thời gian trước, rồi nêu tên người đặt để xác nhận hồ sơ."),
  ("Could you confirm your arrival time for booking {ref}?","Bạn xác nhận giờ đến của đặt phòng mã {ref} giúp tôi nhé?","confirm-arrival","Hỏi giờ đến để chuẩn bị nhận phòng; “Could you…” giữ giọng lịch sự."),
  ("Your confirmation code is {ref}.","Mã xác nhận của bạn là {ref}.","share-reference","“confirmation code” giúp khách nhận ra mã đặt phòng."),
  ("I’ll send the check-in guide by {channel}.","Tôi sẽ gửi hướng dẫn nhận phòng qua {channel}.","send-guide","“send … by + kênh” nêu rõ thông tin được gửi ở đâu."),
  ("If your arrival plans change, just reply to that message.","Nếu kế hoạch đến nơi thay đổi, bạn chỉ cần trả lời tin nhắn đó.","keep-channel-open","“just reply to…” giúp khách biết cách liên hệ lại đơn giản."),
 ],
 [
  ("I can update the booking dates for {guest}.","Tôi có thể cập nhật ngày đặt phòng cho {guest}.","offer-change","“update the dates” diễn tả sửa lịch mà không ám chỉ đã thực hiện."),
  ("Which dates should I check instead for {unit}?","Tôi nên kiểm tra ngày nào thay thế cho {unit}?","ask-new-dates","“instead” làm rõ bạn đang hỏi lịch thay thế."),
  ("I’ll check whether {unit} is free for those dates.","Tôi sẽ kiểm tra {unit} còn trống vào những ngày đó không.","check-new-dates","Kiểm tra tình trạng trống trước khi hứa chuyển ngày."),
  ("The revised total would be {amount}.","Tổng tiền sau khi đổi sẽ là {amount}.","explain-new-total","“would be” báo số tiền dự kiến trước khi xác nhận thay đổi."),
  ("Would you like me to update reservation {ref} now?","Bạn có muốn tôi cập nhật đặt phòng {ref} ngay bây giờ không?","confirm-change","“Should I…?” xin xác nhận trước khi sửa booking."),
 ],
 [
  ("I’ve added your request for {detail}.","Tôi đã ghi nhận yêu cầu của bạn.","acknowledge-request","Hiện tại hoàn thành “I’ve added” báo yêu cầu đã được ghi nhận."),
  ("I’ll check if we can arrange it before {time}.","Tôi sẽ kiểm tra xem có thể chuẩn bị trước {time} không.","check-feasibility","“check if we can…” tránh hứa chắc khi còn phụ thuộc tình trạng phòng."),
  ("If not, we can offer {alternative}.","Nếu không được, bên tôi có thể đề xuất {alternative}.","give-backup","“If not” nối phương án dự phòng trực tiếp với điều kiện vừa nêu."),
  ("I’ve noted it on reservation {ref}.","Tôi đã ghi chú yêu cầu vào đặt phòng {ref}.","record-request","“note it on” nói rõ thông tin được lưu vào hồ sơ nào."),
  ("I’ll message you as soon as {detail} is confirmed.","Tôi sẽ nhắn bạn ngay khi {detail} được xác nhận.","promise-update","“as soon as” nối thời điểm cập nhật với lúc có kết quả."),
 ]
],
"checkin":[
 [
  ("Welcome! Your room is {unit} on the {floor} floor.","Chào mừng bạn! Phòng của bạn là {unit} ở tầng {floor}.","welcome-and-locate","Nói số phòng trước, rồi nêu tầng để khách dễ định hướng."),
  ("The lift is beside {place}.","Thang máy nằm cạnh {place}.","give-direction","“beside” chỉ một mốc gần, hữu ích khi hướng dẫn trong tòa nhà."),
  ("Use the entry code from your check-in message at the main entrance.","Bạn dùng mã cửa trong tin nhắn hướng dẫn nhận phòng ở cửa chính nhé.","explain-access","Nhắc khách lấy mã từ kênh đã xác nhận, không đọc mã truy cập mẫu."),
  ("The Wi-Fi details for unit {unit} are on the welcome card.","Thông tin Wi-Fi của phòng {unit} có trên thẻ chào mừng.","point-to-info","“are on” dùng cho thông tin được in trên một vật."),
  ("Message me here if you need help finding {place}.","Nhắn tôi tại đây nếu bạn cần tìm {place} nhé.","offer-help","“need a hand” là lời mời giúp đỡ thân thiện, tự nhiên."),
 ],
 [
  ("You’re welcome to arrive around {time}.","Bạn có thể đến vào khoảng {time}.","confirm-arrival-window","“around” cho biết thời gian linh hoạt thay vì giờ chính xác."),
  ("The room may not be ready until {ready}.","Phòng có thể chưa sẵn sàng trước {ready}.","set-expectation","“may not … until” báo khả năng và mốc sớm nhất một cách rõ ràng."),
  ("You can leave your bags at {place} meanwhile.","Trong lúc chờ, bạn có thể gửi hành lý tại {place}.","offer-luggage-option","“meanwhile” nối phương án tạm thời với thời gian chờ."),
  ("I’ll message you as soon as {detail} is ready.","Tôi sẽ nhắn bạn ngay khi {detail} sẵn sàng.","promise-room-update","“as soon as” hứa cập nhật ngay khi trạng thái thay đổi."),
  ("Would you like me to text or call you at {time}?","Bạn muốn tôi nhắn tin hay gọi cho bạn lúc {time}?","choose-channel","Cho khách chọn kênh nhận cập nhật để tránh bỏ lỡ."),
 ],
 [
  ("Check-out is by {time}.","Bạn vui lòng trả phòng trước {time}.","state-deadline","“by + giờ” đặt hạn chót; không có nghĩa khách phải ở đến giờ đó."),
  ("Please leave the key at {place}.","Bạn vui lòng để chìa khóa tại {place}.","give-checkout-step","Câu mệnh lệnh thêm “please” để nghe lịch sự."),
  ("I can check whether we can extend check-out for {unit}.","Tôi có thể kiểm tra xem có thể gia hạn giờ trả phòng của {unit} không.","offer-late-checkout","Nói “check whether” trước khi hứa về phòng trống."),
  ("There would be a {fee} fee for the extra hour.","Giờ trả muộn sẽ có phụ phí {fee}.","explain-fee","“there would be” nêu chi phí có điều kiện trước khi khách quyết định."),
  ("Would you like me to request a late check-out for {unit}?","Bạn có muốn tôi gửi yêu cầu trả phòng muộn cho {unit} không?","confirm-request","Xin xác nhận trước khi gửi yêu cầu thay mặt khách."),
 ]
],
"housekeeping":[
 [
  ("Would {time} work for housekeeping?","{time} có thuận tiện để nhân viên dọn phòng ghé không?","offer-cleaning-time","“Would … work?” kiểm tra giờ có phù hợp với khách không."),
  ("We can clean {unit} while you’re out.","Bên tôi có thể dọn phòng bạn khi bạn ra ngoài.","offer-timing","“while you’re out” nối việc dọn với lúc khách không có trong phòng."),
  ("Would you prefer {alternative} instead?","Bạn muốn chọn {alternative} thay vào đó không?","offer-time-option","“instead” nêu một lựa chọn thay thế rõ ràng."),
  ("I’ll note {time} as your preferred time for the team.","Tôi sẽ ghi lại {time} là giờ bạn chọn để báo nhân viên.","record-preference","“note … for the team” chuyển yêu cầu sang người thực hiện."),
  ("We’ll message you once your room is ready after cleaning.","Bên tôi sẽ nhắn khi phòng bạn đã được dọn xong.","close-cleaning-loop","“once” đặt mốc cập nhật sau khi việc hoàn tất."),
 ],
 [
  ("I can bring {item} to your room.","Tôi có thể mang {item} đến phòng bạn.","offer-supply","“bring … to” nói rõ món đồ và nơi giao."),
  ("Would you like it before {time}?","Bạn muốn nhận trước {time} không?","confirm-delivery-time","Hỏi mốc giao để điều phối chính xác."),
  ("I’ll ask housekeeping to prepare {item} for you.","Tôi sẽ nhờ buồng phòng chuẩn bị {item} cho bạn.","assign-request","“ask … to + verb” giao yêu cầu cho đúng nhóm."),
  ("If we’re out of stock, I can offer {alternative}.","Nếu hết món đó, tôi có thể đề xuất {alternative}.","set-alternative","“out of stock” báo hết hàng; câu đưa phương án dự phòng."),
  ("I’ll message you when {item} is on the way to your room.","Tôi sẽ nhắn khi {item} đang được mang đến phòng bạn.","update-delivery","“on the way” báo món đồ đã được chuyển đi."),
 ],
 [
  ("We can pick up the laundry at {time}.","Bên tôi có thể nhận đồ giặt lúc {time}.","arrange-pickup","“pick up” là nhận đồ tại nơi khách đang ở."),
  ("Please leave the laundry bag by the door before {time}.","Bạn vui lòng để túi giặt cạnh cửa trước {time} nhé.","give-preparation-step","“leave it in…” hướng dẫn khách chuẩn bị đồ trước khi nhận."),
  ("The usual turnaround is {duration}.","Thời gian xử lý thông thường là {duration}.","state-turnaround","“turnaround” chỉ thời gian từ lúc nhận đến lúc trả."),
  ("I’ll confirm the laundry charge of {amount} before pickup.","Tôi sẽ xác nhận phí giặt là {amount} trước khi nhận đồ.","confirm-cost","Nói “before” để khách biết phí được xác nhận trước khi xử lý."),
  ("Would you like us to pick up the laundry from {unit}?","Bạn muốn bên tôi nhận đồ giặt tại {unit} chứ?","confirm-service","“go ahead” xin phép thực hiện dịch vụ vừa mô tả."),
 ]
],
"maintenance":[
 [
  ("Thanks for letting me know about {issue}.","Cảm ơn bạn đã báo về {issue}.","acknowledge-fault","“Thanks for letting me know about…” nhận thông tin mà không phán đoán nguyên nhân."),
  ("Is {issue} still causing a problem right now?","Vấn đề đó còn xảy ra lúc này không?","check-current-state","Hỏi hiện trạng trước khi phân loại mức độ khẩn cấp."),
  ("I’ll have maintenance check it at {time}.","Tôi sẽ nhờ kỹ thuật kiểm tra lúc {time}.","schedule-repair","“have + người + verb” dùng khi điều phối người khác xử lý."),
  ("For now, please {safe_step}.","Trước mắt, bạn vui lòng {safe_step}.","give-safe-step","“For now” giới hạn lời khuyên ở bước tạm thời trong lúc chờ."),
  ("I’ll update you once we know what’s going on with {issue}.","Tôi sẽ cập nhật khi biết rõ tình trạng của {issue}.","promise-diagnosis","“once we know” tránh khẳng định nguyên nhân trước khi kiểm tra."),
 ],
 [
  ("Our technician can come by {time}.","Kỹ thuật viên có thể ghé vào {time}.","offer-appointment","“come by” là cách nói tự nhiên khi nhân viên ghé địa điểm."),
  ("Will someone be in {unit} to let them in at {time}?","Lúc {time} có ai ở {unit} để mở cửa cho họ không?","confirm-access","“available to + verb” kiểm tra khả năng có người ở nhà."),
  ("They’ll take a look at {issue} first.","Họ sẽ kiểm tra {issue} trước.","explain-visit","“take a look at” mô tả bước kiểm tra ban đầu, chưa hứa đã sửa xong."),
  ("If that time doesn’t work, we can try {alternative}.","Nếu giờ đó không tiện, mình có thể thử {alternative}.","offer-new-time","“doesn’t work” nói giờ không thuận tiện; “try” giữ lựa chọn linh hoạt."),
  ("Please let me know if {time} works for you.","Bạn cho tôi biết {time} có thuận tiện không nhé.","confirm-slot","“which … you prefer” giúp khách chọn trong các khung giờ vừa nêu."),
 ],
 [
  ("Please stop using {issue} until we’ve checked it.","Bạn vui lòng ngừng sử dụng {issue} cho đến khi bên tôi kiểm tra xong.","prioritize-safety","Khi có nguy cơ, câu đầu tiên hướng khách ra khỏi khu vực có vấn đề."),
  ("I’ve asked the on-call team to check {issue}.","Tôi đã nhờ đội trực kiểm tra {issue}.","escalate-response","Hiện tại hoàn thành “I’ve alerted” báo việc khẩn đã được chuyển đi."),
  ("Is there any immediate risk to you or the room?","Hiện có nguy cơ tức thời nào với bạn hoặc căn phòng không?","check-safety","Hỏi tình trạng an toàn trước khi tiếp tục thu thập chi tiết."),
  ("If there’s immediate danger, call local emergency services.","Nếu có nguy hiểm tức thời, hãy gọi dịch vụ khẩn cấp tại địa phương.","give-emergency-direction","“immediate danger” giới hạn trường hợp cần gọi dịch vụ khẩn cấp."),
  ("I’ll stay in touch while the team checks {issue}.","Tôi sẽ giữ liên lạc trong lúc đội ngũ kiểm tra {issue}.","stay-with-guest","“until” cho biết việc giữ liên lạc kéo dài đến mốc nào."),
 ]
],
"complaints":[
 [
  ("I’m sorry to hear about {issue}.","Tôi rất tiếc khi nghe về {issue}.","apologize-for-impact","Xin lỗi về ảnh hưởng thực tế thay vì đoán lỗi thuộc về ai."),
  ("Could you tell me when you first noticed {issue}?","Bạn cho tôi biết lần đầu nhận thấy {issue} là khi nào được không?","ask-when","“first noticed” hỏi thời điểm bắt đầu để xác định diễn biến."),
  ("I’ll check {detail} right away.","Tôi sẽ kiểm tra {detail} ngay.","take-ownership","“right away” cho thấy bạn bắt đầu xử lý ngay sau khi nghe phản ánh."),
  ("I can arrange {solution} {time}.","Tôi có thể sắp xếp {solution} {time}.","offer-remedy","Nêu phương án và mốc thời gian cụ thể thay vì chỉ nói sẽ xử lý."),
  ("I’ll check back with you {follow_time}.","Tôi sẽ liên hệ lại với bạn {follow_time}.","set-follow-up","“check back” hứa quay lại cập nhật sau khi đã xử lý."),
 ],
 [
  ("Thanks for bringing {issue} to my attention.","Cảm ơn bạn đã báo cho tôi về {issue}.","thank-for-report","“bring … to my attention” xác nhận phản ánh đã được tiếp nhận."),
  ("I can see how {issue} would be frustrating.","Tôi hiểu việc {issue} có thể khiến bạn khó chịu thế nào.","show-empathy","Câu này thừa nhận cảm xúc mà không tranh luận với khách."),
  ("Let me see what we can do about {issue} right now.","Để tôi xem ngay bây giờ bên tôi có thể làm gì về {issue}.","open-resolution","“Let me see…” mở đầu cho bước tìm giải pháp thực tế."),
  ("We can offer {solution} while we sort it out.","Bên tôi có thể bố trí {solution} trong lúc xử lý việc đó.","give-temporary-fix","“while we sort it out” phân biệt giải pháp tạm với xử lý nguyên nhân."),
  ("Would {solution} help tonight?","{solution} có giúp được bạn trong tối nay không?","check-remedy","Hỏi phản hồi để biết phương án tạm thời có phù hợp không."),
 ],
 [
  ("I’ve asked the team to look into {issue}.","Tôi đã nhờ đội ngũ kiểm tra {issue}.","report-action","“look into” là điều tra/kiểm tra vấn đề, chưa đồng nghĩa đã giải quyết."),
  ("They should be there {time}.","Họ dự kiến sẽ có mặt {time}.","give-arrival-estimate","“should be” là thời gian dự kiến; dùng mốc thời gian để đặt kỳ vọng."),
  ("I’ll let you know if the visit time changes.","Tôi sẽ báo bạn nếu giờ ghé kiểm tra thay đổi.","promise-change-update","“if that changes” đặt điều kiện cho lần cập nhật tiếp theo."),
  ("If it’s still happening after {time}, please message me here.","Nếu sau {time} sự cố vẫn còn, bạn nhắn tôi tại đây nhé.","provide-contact-path","“continues” nói vấn đề tiếp diễn; chỉ dẫn khách về một kênh liên hệ."),
  ("I’ll follow up after the team has checked {issue}.","Tôi sẽ liên hệ lại sau khi đội ngũ kiểm tra {issue}.","close-loop","“follow up after” xác định bạn sẽ quay lại sau mốc nào."),
 ]
],
"billing":[
 [
  ("The {period} rent for {unit} is {amount}.","Tiền thuê {period} của {unit} là {amount}.","state-rent","Đưa kỳ thuê, căn hộ và số tiền theo thứ tự để khách dễ kiểm tra."),
  ("It’s due on {date}.","Khoản này đến hạn vào {date}.","state-due-date","“due on” dùng với ngày đến hạn cụ thể."),
  ("You can pay by {method}.","Bạn có thể thanh toán bằng {method}.","give-payment-option","“pay by” giới thiệu phương thức thanh toán."),
  ("I can send the invoice to {channel}.","Tôi có thể gửi hóa đơn qua {channel}.","offer-invoice","Nêu nơi nhận hóa đơn để khách biết bước tiếp theo."),
  ("I’ll send the receipt once the {amount} payment clears.","Tôi sẽ gửi biên nhận khi khoản thanh toán {amount} được xác nhận.","promise-receipt","“once … clears” gắn việc gửi biên nhận với thời điểm tiền được ghi nhận."),
 ],
 [
  ("I can prepare an itemized invoice for {period}.","Tôi có thể chuẩn bị hóa đơn chi tiết cho {period}.","offer-itemized-bill","“itemized invoice” là hóa đơn tách từng khoản."),
  ("Could you confirm the name and email for your {period} invoice?","Bạn xác nhận tên và email để xuất hóa đơn {period} giúp tôi nhé?","collect-billing-details","Hỏi đủ thông tin cần thiết trước khi phát hành hóa đơn."),
  ("I’ll include {detail} as separate line items.","Tôi sẽ tách riêng {detail} thành từng dòng.","explain-breakdown","“line items” chỉ các khoản được liệt kê riêng trên hóa đơn."),
  ("You’ll receive it {time}.","Bạn sẽ nhận được {time}.","give-delivery-time","Nêu rõ mốc khách có thể nhận hóa đơn."),
  ("Let me know if you need any changes to {detail}.","Bạn cho tôi biết nếu cần chỉnh sửa gì ở {detail} nhé.","invite-correction","Mời khách báo sai sót sau khi nhận chứng từ."),
 ],
 [
  ("Would you like to extend your stay past {date}?","Bạn có muốn kéo dài kỳ lưu trú sau {date} không?","ask-extension","“extend … past” hỏi về việc ở tiếp sau ngày kết thúc hiện tại."),
  ("I’ll check availability for {unit} first.","Trước tiên tôi sẽ kiểm tra {unit} còn trống không.","check-extension","Kiểm tra phòng trước khi xác nhận gia hạn."),
  ("The updated rate would be {amount}.","Mức giá mới sẽ là {amount}.","state-new-rate","“would be” báo mức giá dự kiến để khách cân nhắc."),
  ("The deposit for {unit} is processed after the room check.","Khoản cọc của {unit} được xử lý sau khi kiểm tra phòng.","explain-deposit-process","Nói rõ điều kiện kiểm tra trước khi xử lý hoàn cọc."),
  ("Would you like me to prepare an updated agreement for {unit}?","Bạn có muốn tôi chuẩn bị thỏa thuận cập nhật cho {unit} không?","confirm-document","Xin phép trước khi soạn giấy tờ gia hạn."),
 ]
],
"safety":[
 [
  ("Thanks for reporting {issue}.","Cảm ơn bạn đã báo về {issue}.","acknowledge-safety-report","Nhận báo cáo trước khi điều phối người xử lý."),
  ("Could you tell me where you are in the building?","Bạn đang ở khu vực nào trong tòa nhà?","locate-incident","Hỏi vị trí hiện tại để đội tòa nhà biết nơi liên hệ hoặc hỗ trợ."),
  ("I’ll ask the building team to check it now.","Tôi sẽ nhờ đội ngũ tòa nhà kiểm tra ngay.","alert-security","“now” đặt hành động ngay ở hiện tại."),
  ("Please stay somewhere safe while they look into it.","Bạn hãy ở nơi an toàn trong lúc đội ngũ kiểm tra nhé.","keep-distance","Ưu tiên vị trí an toàn mà không đưa chỉ dẫn quá cụ thể khi chưa rõ tình huống."),
  ("I’ll update you once they’ve checked.","Tôi sẽ cập nhật sau khi họ kiểm tra xong.","confirm-clearance","Hẹn cập nhật sau khi việc kiểm tra hoàn tất."),
 ],
 [
  ("I can help with {issue}.","Tôi có thể hỗ trợ bạn về {issue}.","offer-access-help","Mở đầu bằng việc xác nhận nhu cầu hỗ trợ cụ thể."),
  ("Are you near {location} right now?","Hiện bạn đang ở gần {location} không?","check-location","Xác định khách đang ở đâu trước khi hướng dẫn ra vào."),
  ("I’ll check the building procedure for {issue}.","Tôi sẽ kiểm tra quy trình của tòa nhà cho việc này.","check-building-procedure","Kiểm tra quy trình trước khi hướng dẫn khách."),
  ("The front desk can help you at {location}.","Lễ tân có thể hỗ trợ bạn tại {location}.","offer-front-desk-help","Nêu đầu mối hỗ trợ và địa điểm cụ thể."),
  ("I’ll confirm the next step before you head over.","Tôi sẽ xác nhận bước tiếp theo trước khi bạn qua đó.","confirm-next-step","Chốt bước tiếp theo sau khi kiểm tra quy định."),
 ],
 [
  ("Please move to a safe area and call {emergency}.","Bạn vui lòng đến nơi an toàn và gọi {emergency}.","direct-emergency-action","Câu ngắn ưu tiên hành động an toàn và dịch vụ khẩn cấp địa phương."),
  ("I’ve alerted the building team about {issue} as well.","Tôi cũng đã báo đội ngũ tòa nhà về {issue}.","report-escalation","“as well” cho biết ngoài cuộc gọi khẩn cấp, đội tòa nhà cũng đã được báo."),
  ("Is everyone safe near {location}, and does anyone need medical help?","Mọi người gần {location} có an toàn không, có ai cần trợ giúp y tế không?","check-persons","Kiểm tra an toàn và người bị thương bằng hai câu hỏi ngắn."),
  ("Stay on the line while I guide you to {location}.","Bạn cứ giữ máy trong lúc tôi hướng dẫn đến {location} nhé.","keep-contact","“stay on the line” giữ kết nối điện thoại trong lúc hỗ trợ."),
  ("I’ll meet the responders at {location}.","Tôi sẽ đón lực lượng hỗ trợ tại {location}.","coordinate-responders","Nêu điểm gặp để hướng dẫn lực lượng đến đúng chỗ."),
 ]
],
"team":[
 [
  ("Can you check {task} in {unit} before {deadline}?","Bạn kiểm tra {task} ở {unit} trước {deadline} giúp tôi nhé?","assign-task","“Can you check… before…?” giao việc và nêu rõ địa điểm cùng hạn chót."),
  ("Let me know if you run into any issues with {task}.","Nếu gặp vướng mắc với {task}, bạn báo tôi nhé.","request-exception","Mời báo ngoại lệ thay vì để công việc dừng mà không cập nhật."),
  ("The next guest arrives at {time}.","Khách tiếp theo đến lúc {time}.","share-context","Nêu mốc khách đến để nhân viên hiểu mức độ ưu tiên."),
  ("Could you send a photo of {unit} once it’s ready?","Khi {unit} sẵn sàng, bạn gửi ảnh giúp tôi được không?","request-proof","“once it’s ready” chỉ thời điểm cần gửi ảnh xác nhận."),
  ("I’ll add the final status for {task} to the shift log.","Tôi sẽ ghi trạng thái cuối của {task} vào sổ bàn giao ca.","record-completion","“after that” nối bước ghi nhận sau khi đã kiểm tra xong."),
 ],
 [
  ("The {vendor} is expected at {time}.","{vendor} dự kiến sẽ đến lúc {time}.","share-arrival","“is expected at” báo giờ đến dự kiến của nhà cung cấp."),
  ("Please confirm {vendor} can access {location}.","Bạn xác nhận {vendor} có thể vào {location} giúp tôi nhé.","coordinate-access","Nêu rõ cần xác nhận lối tiếp cận nào."),
  ("They’ll bring the parts needed to finish {task}.","Họ sẽ mang linh kiện cần thiết để hoàn tất {task}.","explain-visit","“parts for” cho biết nhà cung cấp cần mang đồ gì."),
  ("Please tell reception if {vendor} is delayed.","Nếu {vendor} bị trễ, bạn báo lễ tân nhé.","report-delay","“running late” là cách nói thường dùng về việc đến trễ."),
  ("I’ll update the guest once {task} is complete.","Tôi sẽ cập nhật cho khách khi {task} hoàn tất.","own-guest-update","Tách trách nhiệm cập nhật khách khỏi phần điều phối nội bộ."),
 ],
 [
  ("The guest is waiting on {task}.","Khách đang chờ xử lý {task}.","handoff-status","“waiting on” nói điều khách đang chờ; dùng trong trao đổi nội bộ."),
  ("We’ve already tried {detail}.","Bên tôi đã thử {detail}.","share-attempted-fix","Hiện tại hoàn thành cho biết bước xử lý đã thử trước ca này."),
  ("The issue is still happening in {unit}.","Sự cố vẫn đang xảy ra ở {unit}.","state-current-status","“still happening” nhấn mạnh vấn đề chưa được giải quyết."),
  ("Could you take over and check it by {deadline}?","Bạn nhận xử lý tiếp và kiểm tra trước {deadline} được không?","transfer-ownership","“take over” chuyển trách nhiệm xử lý sang người nhận."),
  ("Please add the result for {task} in {unit} to the shared log.","Bạn ghi kết quả {task} ở {unit} vào nhật ký chung giúp tôi nhé.","close-handoff","Nêu nơi lưu kết quả để ca sau tra cứu được."),
 ]
],
"messaging":[
 [
  ("Thanks for calling about {topic}.","Cảm ơn bạn đã gọi về {topic}.","answer-call","Nêu lý do cuộc gọi để bắt đầu trao đổi đúng chủ đề."),
  ("Could I confirm the arrival date for your booking?","Bạn cho tôi xác nhận ngày đến trong đặt phòng nhé?","confirm-identity-detail","Hỏi thông tin liên quan trực tiếp đến việc sắp xếp phòng."),
  ("I’ll check {detail} for you.","Tôi sẽ kiểm tra {detail} giúp bạn.","promise-check","“check … for you” nhận bước kiểm tra mà không khẳng định kết quả sớm."),
  ("I can send the details by {channel}.","Tôi có thể gửi thông tin qua {channel}.","offer-written-details","Đề nghị gửi thông tin bằng văn bản để khách dễ mở lại."),
  ("Would you like me to call or message you about {topic}?","Bạn muốn tôi gọi hay nhắn cho bạn về {topic}?","choose-contact-channel","Đưa ra hai kênh liên hệ rõ ràng để khách chọn."),
 ],
 [
  ("Hi {guest}, I’ve sent an update about {topic}.","Chào {guest}, tôi đã gửi cập nhật về {topic}.","send-confirmation","Mở tin nhắn bằng tên khách rồi nêu ngay thông tin được xác nhận."),
  ("I’ve attached {link} to this message.","Tôi đã đính kèm {link} trong tin nhắn này.","share-link","Dấu hai chấm làm phần hướng dẫn hoặc liên kết dễ nhận ra."),
  ("If you need anything else about {topic}, just reply here.","Nếu cần thêm gì về {topic}, bạn cứ trả lời tại đây nhé.","invite-reply","“reply if…” cho khách biết cách yêu cầu thay đổi."),
  ("I’ll be available {time}.","Tôi sẽ trực {time}.","state-availability","Nêu rõ khi nào bạn có thể phản hồi."),
  ("Thanks for getting in touch about {topic}, {guest}.","Cảm ơn {guest} đã liên hệ về {topic}.","close-warmly","Câu chúc ngắn kết thúc tin nhắn trước chuyến đi một cách thân thiện."),
 ],
 [
  ("How has everything been in {unit} so far?","Cho đến giờ mọi thứ ở {unit} thế nào rồi?","check-experience","“so far” hỏi về trải nghiệm tính đến hiện tại."),
  ("I’m glad everything is working well in {unit}.","Tôi rất vui vì mọi thứ ở {unit} đang hoạt động tốt.","respond-positively","Phản hồi ngắn xác nhận bạn đang lắng nghe điều tích cực."),
  ("Is there anything we can do to make your stay more comfortable?","Bên tôi có thể làm gì để bạn nghỉ ngơi thoải mái hơn không?","invite-feedback","Câu hỏi mở mời góp ý mà không giả định khách đang phàn nàn."),
  ("I can take care of {request} today.","Hôm nay tôi có thể xử lý {request}.","offer-help","“take care of” nhận xử lý một yêu cầu cụ thể."),
  ("Just message me here if you need anything else during your stay, {guest}.","Nếu cần thêm gì trong kỳ lưu trú, bạn cứ nhắn tôi tại đây nhé, {guest}.","keep-door-open","“anything else” mở lời cho các nhu cầu tiếp theo."),
 ]
]
}

FACTS = {
"rooms":{"guest":["Maya","Daniel","Linh","Mr. Carter"],"dates":["June 8 to 14","July 2 to 9","August 12 to 19","September 3 to 10"],"rate":["1.25 million VND a night","15 million VND a month","900,000 VND a night","12.5 million VND a month"],"duration":["two weeks","a month","six nights","the whole summer"],"priority":["a quiet workspace","step-free access","a lower monthly rate","a balcony"],"unit":["furnished studio","one-bedroom unit","courtyard-facing room","lower-floor apartment"],"alternative":["a studio on the fourth floor","a furnished one-bedroom","a weekly booking","the larger corner unit"],"detail":["weekly cleaning and Wi-Fi","a kitchenette and a work desk","utilities and weekly housekeeping","a balcony and extra storage"],"time":["Tuesday at 4 p.m.","Wednesday at 10 a.m.","Friday after 2 p.m.","Saturday morning"],"amount":["14.5 million VND","1.8 million VND","850,000 VND","16 million VND"],"dates_range":["June 8 to 14","July 2 to 9","August 12 to 19","September 3 to 10"],"fee":["250,000 VND","300,000 VND","400,000 VND","200,000 VND"],"priority2":["more storage","a shorter commute","a kitchen","a quiet view"]},
"booking":{"guest":["Maya Chen","Daniel Lee","Linh Nguyen","Alex Morgan"],"dates":["June 8 to 14","July 2 to 9","August 12 to 19","September 3 to 10"],"ref":["TH-2841","TH-3157","TH-4082","TH-5196"],"channel":["WhatsApp","email","the booking chat","text message"],"unit":["unit 204","unit 305","the studio","the one-bedroom"],"amount":["8.75 million VND","14.5 million VND","1.2 million VND","16 million VND"],"time":["6 p.m.","10:30 p.m.","Friday afternoon","the day before arrival"],"detail":["an extra bed","a higher-floor room","a late arrival","a vegetarian breakfast nearby"],"alternative":["a room on the next floor","a later check-in slot","a one-night extension","a secure payment link"]},
"checkin":{"unit":["204","305","408","512"],"floor":["second","third","fourth","fifth"],"place":["the front desk","the courtyard entrance","the glass door","the luggage room"],"access":["4821","7350","9164","2608"],"time":["2 p.m.","5:30 p.m.","11 a.m.","midnight"],"ready":["2 p.m.","3 p.m.","4 p.m.","5 p.m."],"contact":["+84 90 123 4567","the night manager","reception","the on-call host"],"alternative":["a 3 p.m. visit","a luggage drop-off","a call when the room is ready","a key pickup at reception"],"fee":["200,000 VND","300,000 VND","250,000 VND","350,000 VND"]},
"housekeeping":{"time":["2 p.m.","4 p.m.","6 p.m.","10 a.m."],"alternative":["tomorrow morning","after 5 p.m.","a quick towel drop-off","Thursday instead"],"item":["two extra bath towels","a blanket and two pillows","a pack of toilet paper","a fresh set of bed linen"],"duration":["one business day","by 6 p.m.","the next morning","about 24 hours"],"detail":["the room while you’re out","the linen bag by your door","the laundry pickup time","the housekeeping schedule"],"request":["a room tidy","fresh towels","the laundry pickup","an extra pillow"]},
"maintenance":{"issue":["the air conditioner","the water heater","the Wi-Fi router","the bathroom faucet","the door lock","the fridge","the hallway light","the elevator"],"unit":["unit 204","unit 305","the bathroom","the hallway","the laundry room","the main entrance"],"time":["2 p.m.","4:30 p.m.","7 p.m.","tomorrow morning"],"alternative":["tomorrow at 9 a.m.","a room move for tonight","a portable fan","a backup Wi-Fi router"],"safe_step":["switch off the unit at the breaker","keep the floor clear","use the spare key for now","avoid using that outlet"],"detail":["the temperature setting","the water supply","the router lights","the lock mechanism"],"solution":["a room move for tonight","a portable fan","a temporary hotspot","a replacement key"],"emergency":["the technician","building security","the on-call manager","the maintenance lead"]},
"complaints":{"issue":["the room cleaning","noise from upstairs","the extra charge","the missing kitchen items","the air conditioner noise","the slow Wi-Fi","the check-in delay","the stained towels"],"detail":["the bathroom and kitchenette","the room number and time","the charge on your statement","the router connection"],"solution":["a fresh set of towels","a room check and a temporary fan","a corrected invoice","a quiet room","a housekeeping return visit","a backup hotspot"],"time":["within 30 minutes","by 5 p.m.","before dinner","within the hour"],"follow_time":["at 5 p.m.","after the team visits","this evening","tomorrow morning"],"alternative":["a room move for tonight","a temporary fan","a corrected statement","a fresh set of supplies"]},
"billing":{"period":["monthly","weekly","June","the final"],"unit":["unit 204","unit 305","the studio","the one-bedroom"],"amount":["15 million VND","8.5 million VND","1.2 million VND","250,000 VND"],"date":["June 5","the 10th of each month","Friday","check-out day"],"method":["bank transfer or card","a secure payment link","the bank details on the invoice","cash at reception"],"channel":["your billing email","WhatsApp","the booking email","the company contact"],"detail":["the room charge and cleaning fee","the rent and deposit","the utilities and service fee","the extra night and tax"],"time":["the end of the day","tomorrow at noon","within two business days","before the next billing cycle"]},
"safety":{"issue":["noise after quiet hours","a lost key","a visitor at the entrance","water in the hallway","a burning smell","a power cut","a blocked exit","an unattended bag"],"location":["the west stairwell","the second-floor hallway","the main entrance","the lobby near reception","the basement parking area"],"emergency":["local emergency services","the fire department","the building emergency line","the local ambulance service"],"time":["9 p.m.","quiet hours","after midnight","the next 10 minutes"],"contact":["the front desk","building security","the night manager","the on-call host"]},
"team":{"task":["the turnover clean","the lock check","the linen restock","the maintenance visit","the room inspection","the luggage handoff"],"unit":["unit 204","unit 305","level four","the lobby","the service entrance"],"deadline":["2 p.m.","the next check-in","the end of this shift","noon tomorrow"],"time":["10:30 p.m.","1 p.m.","6 p.m.","the morning shift"],"vendor":["the plumber","the locksmith","the linen supplier","the appliance technician"],"detail":["the filter","the spare key","the delivery slip","the room checklist"]},
"messaging":{"topic":["your arrival time","the booking details","the room status","the parking entrance","your luggage request","the late check-out"],"guest":["Maya","Daniel","Linh","Alex"],"detail":["the room status","the map pin","the check-in guide","the housekeeping update"],"channel":["WhatsApp","the booking chat","email","a text message"],"time":["5 p.m.","before noon","within the hour","after check-in"],"request":["a fresh towel delivery","a quiet-room request","the parking directions","the late check-out"],"link":["the check-in guide","the map pin","the building rules","the payment page"]}
}

GOALS = {
"rooms":"Tìm hiểu nhu cầu, báo lựa chọn phù hợp và chốt bước tiếp theo về phòng.",
"booking":"Xác nhận chi tiết đặt phòng, xử lý thay đổi và thông báo rõ bước kế tiếp.",
"checkin":"Hướng dẫn khách đến đúng phòng, vào tòa nhà và biết cách liên hệ hỗ trợ.",
"housekeeping":"Ghi nhận yêu cầu, thống nhất thời gian và xác nhận khi nhân viên hoàn tất.",
"maintenance":"Làm rõ hiện trạng, sắp xếp người kiểm tra và cập nhật sau khi xác định nguyên nhân.",
"complaints":"Lắng nghe tác động, đưa phương án khả thi và chủ động theo dõi kết quả.",
"billing":"Giải thích khoản tiền và thời hạn rõ ràng, rồi xác nhận chứng từ hoặc bước xử lý.",
"safety":"Xác định vị trí, ưu tiên an toàn và điều phối đúng người hỗ trợ.",
"team":"Giao việc nội bộ có người phụ trách, mốc thời gian và cách xác nhận hoàn tất.",
"messaging":"Trả lời ngắn gọn qua kênh phù hợp và giữ liên lạc đến khi yêu cầu được xử lý."
}

def val(category: str, key: str, index: int, default: str) -> str:
    values=FACTS.get(category,{}).get(key)
    return values[index % len(values)] if values else default

def vi_slot(category: str, key: str, value: str) -> str:
    """Render concise Vietnamese equivalents for English scenario slots."""
    fixed={
        'channel':{'WhatsApp':'WhatsApp','email':'email','the booking chat':'khung chat đặt phòng','text message':'tin nhắn','your billing email':'email nhận hóa đơn','the booking email':'email đặt phòng','the company contact':'đầu mối công ty'},
        'period':{'monthly':'theo tháng','weekly':'theo tuần','June':'tháng 6','the final':'kỳ cuối'},
        'method':{'bank transfer or card':'chuyển khoản hoặc thẻ','a secure payment link':'liên kết thanh toán bảo mật','the bank details on the invoice':'thông tin ngân hàng trên hóa đơn','cash at reception':'tiền mặt tại quầy lễ tân'},
        'vendor':{'the plumber':'thợ sửa ống nước','the locksmith':'thợ khóa','the linen supplier':'nhà cung cấp đồ vải','the appliance technician':'kỹ thuật viên thiết bị'},
        'location':{'the west stairwell':'cầu thang phía tây','the second-floor hallway':'hành lang tầng hai','the main entrance':'cửa chính','the lobby near reception':'sảnh gần quầy lễ tân','the basement parking area':'khu đỗ xe tầng hầm','the kitchen area':'khu vực bếp','the affected hallway':'hành lang xảy ra sự cố','the affected floor':'tầng xảy ra sự cố','a designated outdoor area':'khu vực ngoài trời được chỉ định','the pool entrance':'lối vào hồ bơi'},
        'place':{'the front desk':'quầy lễ tân','the courtyard entrance':'lối vào sân trong','the glass door':'cửa kính','the luggage room':'phòng giữ hành lý','the lobby':'sảnh'},
        'emergency':{'local emergency services':'dịch vụ khẩn cấp tại địa phương','the fire department':'cứu hỏa','the building emergency line':'đường dây khẩn cấp của tòa nhà','the local ambulance service':'cấp cứu địa phương'},
        'priority':{'a quiet workspace':'chỗ làm việc yên tĩnh','step-free access':'lối đi không bậc','a lower monthly rate':'giá thuê tháng thấp hơn','a balcony':'ban công'},
        'detail':{'weekly cleaning and Wi-Fi':'dọn phòng hằng tuần và Wi-Fi','a kitchenette and a work desk':'bếp nhỏ và bàn làm việc','utilities and weekly housekeeping':'các tiện ích và dịch vụ dọn phòng hằng tuần','a balcony and extra storage':'ban công và chỗ chứa đồ rộng hơn'},
        'alternative':{'a studio on the fourth floor':'studio ở tầng bốn','a furnished one-bedroom':'căn hộ một phòng ngủ có nội thất','a weekly booking':'đặt phòng theo tuần','the larger corner unit':'căn góc rộng hơn','tomorrow morning':'sáng mai','after 5 p.m.':'sau 5 giờ chiều','a quick towel drop-off':'mang khăn đến nhanh','Thursday instead':'thứ Năm','a morning visit':'buổi ghé vào buổi sáng'},
        'solution':{'a fresh set of towels':'một bộ khăn sạch','a room check and a temporary fan':'kiểm tra phòng và mang quạt tạm','a corrected invoice':'hóa đơn đã chỉnh sửa','a quiet room for tonight':'phòng yên tĩnh trong tối nay','a housekeeping return visit':'nhân viên buồng phòng quay lại','a backup hotspot':'thiết bị phát Wi-Fi dự phòng'},
        'safe_step':{'switch off the unit at the breaker':'tắt cầu dao của thiết bị','keep the floor clear':'giữ sàn khô thoáng','use the spare key for now':'tạm dùng chìa khóa dự phòng','avoid using that outlet':'tạm ngừng dùng ổ điện đó'},
        'floor':{'second':'2','third':'3','fourth':'4','fifth':'5'},
    }
    if value in fixed.get(key,{}): return fixed[key][value]
    if key in {'rate','amount','fee'}:
        result=value.replace('million VND','triệu đồng').replace('VND','đồng').replace('a night','mỗi đêm').replace('a month','mỗi tháng')
        return result.replace('.',',')
    if key in {'time','ready','time2','follow_time','deadline','date','dates','dates_range'}:
        result=value
        weekdays={'Monday':'thứ Hai','Tuesday':'thứ Ba','Wednesday':'thứ Tư','Thursday':'thứ Năm','Friday':'thứ Sáu','Saturday':'thứ Bảy','Sunday':'Chủ nhật'}
        months={'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
        import re
        for month,number in months.items():
            result=re.sub(rf'\b{month} (\d+) to (\d+)\b',rf'ngày \1–\2 tháng {number}',result)
            result=re.sub(rf'\b{month} (\d+)\b',rf'ngày \1 tháng {number}',result)
        for source,target in weekdays.items(): result=result.replace(source,target)
        for month,number in months.items(): result=result.replace(month,f'tháng {number}')
        result=result.replace(' to ','–').replace(' at ',' lúc ').replace('at ','lúc ').replace('around ','khoảng ').replace('after ','sau ').replace('before ','trước ').replace('by ','trước ')
        def clock_vi(match):
            hour=int(match.group(1)); minute=match.group(2) or ''
            period=match.group(3).lower()
            if period=='p.m.': label='trưa' if hour==12 else 'chiều' if hour<6 else 'tối'
            else: label='nửa đêm' if hour==12 else 'sáng'
            return f"{hour}{minute} giờ {label}"
        result=re.sub(r'\b(\d{1,2})(:\d{2})?\s*(a\.m\.|p\.m\.)',clock_vi,result,flags=re.I)
        result=result.replace('midnight','nửa đêm').replace('morning','buổi sáng')
        result=result.replace('the 10th of each month','ngày 10 hằng tháng').replace('check-out day','ngày trả phòng').replace('quiet hours','giờ yên tĩnh').replace('the next check-in','lượt nhận phòng tiếp theo').replace('the end of this shift','cuối ca này').replace('the end of the day','cuối ngày').replace('within two business days','trong vòng hai ngày làm việc').replace('within 30 minutes','trong vòng 30 phút').replace('within the hour','trong vòng một giờ').replace('one business day','một ngày làm việc').replace('about 24 hours','khoảng 24 giờ').replace('after the team visits','sau khi đội ngũ ghé kiểm tra').replace('tomorrow at noon','trưa mai').replace('tomorrow morning','sáng mai').replace('this evening','tối nay').replace('Saturday morning','sáng thứ Bảy')
        return result
    if key=='duration':
        return {'two weeks':'hai tuần','a month':'một tháng','six nights':'sáu đêm','the whole summer':'suốt mùa hè','one business day':'một ngày làm việc','by 6 p.m.':'trước 6 giờ chiều','the next morning':'sáng hôm sau','about 24 hours':'khoảng 24 giờ'}.get(value,'khoảng thời gian này')
    if key in {'guest','name','ref','access'}: return value
    defaults={
        'topic':'nội dung này','unit':'căn hộ này','detail':'thông tin liên quan','alternative':'lựa chọn khác','duration':'thời gian lưu trú này','priority':'nhu cầu của bạn',
        'issue':'sự cố này','solution':'phương án xử lý','item':'món đồ đó','request':'yêu cầu này','task':'đầu việc này','link':'hướng dẫn này',
        'contact':'đầu mối trực','priority2':'ưu tiên đó','feature':'tiện nghi đó','option':'phương án khác','action':'bước tiếp theo','next':'bước tiếp theo',
    }
    if key=='detail':
        return {'rooms':'các tiện nghi đi kèm','booking':'yêu cầu này','checkin':'thông tin này','housekeeping':'đồ dùng cần thiết','maintenance':'tình trạng này','complaints':'khu vực đó','billing':'các khoản trên hóa đơn','safety':'thông tin sự cố','team':'thiết bị cần kiểm tra','messaging':'thông tin này'}.get(category,defaults[key])
    if key=='topic' and category=='rooms': return 'nhu cầu thuê phòng này'
    if key=='unit':
        if category=='checkin' and value.isdigit(): return value
        if value.startswith('unit '): return 'căn '+value.split()[-1]
        if category=='rooms':
            return {'furnished studio':'studio có nội thất','one-bedroom':'căn hộ một phòng ngủ','monthly stay':'căn hộ thuê theo tháng','quiet room':'phòng yên tĩnh','studio':'studio','accessible room':'căn hộ dễ tiếp cận','room for three guests':'phòng cho ba khách','pet-friendly unit':'căn hộ cho phép thú cưng'}.get(value,'căn hộ này')
        if category=='booking' and value in {'the studio','the one-bedroom'}: return 'căn hộ này'
        return defaults[key]
    if key=='place': return defaults['unit']
    if key=='duration': return 'thời gian xử lý này' if category=='housekeeping' else defaults[key]
    if key=='location': return 'khu vực đó'
    if key=='priority2': return 'nhu cầu đó'
    if key=='safe_step': return 'tạm ngừng sử dụng thiết bị này'
    if key=='period': return 'kỳ thuê này'
    return defaults.get(key,'thông tin này')

def render_vi(category: str, template: str, facts: dict[str,str]) -> str:
    translated={key:vi_slot(category,key,value) for key,value in facts.items() if key!='topic_vi'}
    translated['topic']={
        'rooms':'nhu cầu thuê phòng','booking':'đặt phòng của bạn','checkin':'việc nhận phòng',
        'housekeeping':'yêu cầu của bạn','maintenance':'sự cố này','complaints':'việc này',
        'billing':'khoản tiền này','safety':'việc này','team':'đầu việc này','messaging':'yêu cầu này',
    }.get(category,facts.get('topic_vi',translated.get('topic','nội dung này')))
    rendered=template.format(**translated)
    return rendered[:1].upper()+rendered[1:] if rendered else rendered

def scenario_facts(category: str, index: int, title: str, topic: str, detail: str, alternative: str) -> dict[str,str]:
    """Use case-specific facts first, then fill only template fields with safe defaults."""
    fields={
        'guest':'the guest','dates':'June 8 to 14','date':'June 5','dates_range':'June 8 to 14',
        'duration':'two weeks','rate':'1.2 million VND a night','amount':'1.2 million VND',
        'method':'bank transfer or card','channel':'WhatsApp','ref':'TH-2841','time':'4 p.m.',
        'ready':'3 p.m.','floor':'third','place':'the front desk','access':'4821',
        'contact':'the on-call host','fee':'250,000 VND','item':'two extra towels',
        'request':'the request','issue':'the issue','safe_step':'keep the floor clear',
        'solution':'a technician visit','priority':'a quiet workspace','priority2':'more storage',
        'time2':'5 p.m.','follow_time':'5 p.m.','period':'monthly','location':'the lobby','emergency':'local emergency services',
        'task':topic,'deadline':'2 p.m.','vendor':'the technician','link':'the check-in guide',
        'name':'Maya','feature':detail,'option':alternative,'when':'Tuesday at 4 p.m.',
        'time_slot':'2 p.m.','staff':'housekeeping','action':'send the details','next':'send the booking details',
        'room':'unit 204','wifi':'the guest Wi-Fi network','guest_name':'Maya Chen','unit':'unit 204',
    }
    for key in fields:
        fields[key]=val(category,key,index,fields[key])
    # The case record is the source of truth for the conversation's subject and options.
    fields.update({'topic':topic,'detail':detail,'alternative':alternative,'feature':detail,'option':alternative})
    fields['topic_vi']=title.lower()
    if category in {'maintenance','complaints','safety'}: fields['issue']=topic
    if category=='housekeeping':
        fields['item']=topic
        if fields['alternative'].lower().endswith(' instead'):
            fields['alternative']=fields['alternative'][:-8]
    if category=='team': fields['task']=re.sub(r'\s+in unit \d+\b','',topic,flags=re.I)
    if category=='maintenance':
        title_key=(title+' '+topic).lower()
        if 'outlet' in title_key: fields['safe_step']='avoid using that outlet'
        elif 'faucet' in title_key or 'nước tràn' in title_key: fields['safe_step']='move away from the wet area and keep the floor clear'
        elif 'elevator' in title_key or 'thang máy' in title_key: fields['safe_step']='stay clear of the elevator doors and call building security'
        elif 'power' in title_key or 'mất điện' in title_key: fields['safe_step']='avoid touching electrical equipment'
        elif 'smoke' in title_key or 'báo khói' in title_key: fields['safe_step']='leave the area and call local emergency services if you see smoke'
    if category=='safety':
        safety_case=(title+' '+topic).lower()
        if 'burning smell' in safety_case or 'mùi khét' in safety_case: fields['location']='the kitchen area'
        elif 'water' in safety_case or 'nước tràn' in safety_case: fields['location']='the affected hallway'
        elif 'power cut' in safety_case or 'mất điện' in safety_case: fields['location']='the affected floor'
        elif 'smoking' in safety_case or 'hút thuốc' in safety_case: fields['location']='a designated outdoor area'
        elif 'pool' in safety_case or 'hồ bơi' in safety_case: fields['location']='the pool entrance'
        elif 'lost-property' in safety_case or 'để quên đồ' in safety_case: fields['location']='the lobby near reception'
    if category=='rooms':
        room=topic.removeprefix('a ').removeprefix('an ')
        room=re.split(r'\s+(?:for|near|with|on|facing)\b',room,maxsplit=1)[0]
        room={'monthly stay':'apartment','room for three guests':'room for three guests'}.get(room,room)
        fields['unit']=room or 'furnished studio'
        # The three room flows ask about duration, then compare a rate, then discuss
        # features. Avoid putting a view or amenity in a price sentence.
        fields['detail']=val(category,'detail',index,detail)
        fields['alternative']=val(category,'alternative',index,alternative)
        fields['priority']=val(category,'priority',index,detail)
    if category=='billing' and fields['period'].startswith('the '):
        fields['period']=fields['period'][4:]
    if category=='team' and fields['vendor'].startswith('the '):
        fields['vendor']=fields['vendor'][4:]
    return fields

def slug(text: str) -> str:
    import unicodedata
    text=unicodedata.normalize('NFD',text.lower())
    text=''.join(ch for ch in text if unicodedata.category(ch)!='Mn')
    return re.sub(r'[^a-z0-9]+','-',text).strip('-')

common_ids={p['id'] for p in CORE_PHRASES}
host_ids=[f"p{index:03d}" for index in range(1,1201) if f"p{index:03d}" not in common_ids]
if len(host_ids)!=575: raise ValueError(f'Expected 575 replaceable workplace IDs, found {len(host_ids)}')

phrases=[dict(p) for p in CORE_PHRASES if p['categoryId'] in COMMON_CATEGORIES]
for phrase in phrases:
    if phrase['categoryId']=='reflex':
        phrase['register']='guest-facing clear-professional'
        phrase['usageNote']='Cụm Everyday/Reflex dùng lại nếu phù hợp khi nghe, hỏi lại hoặc xác nhận với khách lưu trú.'

category_meta=[dict(c) for c in CORE_CATEGORIES if c['id'] in COMMON_CATEGORIES]
for index,category in enumerate(category_meta,1): category['priority']=index
subcategories=[dict(s) for s in CORE_SUBCATEGORIES if s['categoryId'] in COMMON_CATEGORIES]
host_lessons=[]
patterns={p['id']:dict(p) for p in CORE_PATTERNS if any(phrase['patternId']==p['id'] for phrase in phrases)}
for phrase in phrases:
    patterns.setdefault(phrase['patternId'], {'id':phrase['patternId'],'name':phrase['pattern'],'example':phrase['en'],'categoryId':phrase['categoryId'],'usage':phrase['memoryTip']})
host_pointer=0
category_queue={}
for rank,category in enumerate(CATEGORY_DATA,3):
    category['priority']=rank
    scenarios=[]
    cat_phrase_count=0
    for index,(title,topic,detail,alternative) in enumerate(category['cases']):
        flow=FLOW_ASSIGNMENTS[category['id']][index]
        flow_id=f"{category['id']}-flow-{flow+1}"
        sub_id=flow_id
        template=FLOW_TEMPLATES[category['id']][flow]
        context=f"Bạn đang xử lý với khách lưu trú hoặc đồng nghiệp về tình huống: {title.lower()}."
        facts=scenario_facts(category['id'],index,title,topic,detail,alternative)
        ids=host_ids[host_pointer:host_pointer+5]
        if len(ids)!=5: raise ValueError('Host ID allocation ended before all scenarios were written')
        host_pointer+=5
        step_records=[]
        for turn,(en_template,vi_template,intent,tip) in enumerate(template,1):
            try:
                en=en_template.format(**facts).replace('p.m..','p.m.').replace('a.m..','a.m.')
                vi=render_vi(category['id'],vi_template,facts)
            except KeyError as error:
                raise ValueError(f'Missing template field {error} in {category["id"]}/{title}')
            follow=(template[turn][0].format(**facts) if turn<5 else f"I’ll send you an update about {topic} by {facts['time']}.").replace('p.m..','p.m.').replace('a.m..','a.m.')
            phrase_id=ids[turn-1]
            pattern_id=f"host-{category['id']}-{index+1:02d}-{turn}"
            pattern=re.sub(r'\{[^}]+\}', '…', en_template)
            phrase={
                'id':phrase_id,'day':len(host_lessons)+1,'topic':title,'focus':intent,'en':en,'vi':vi,
                'context':context,'follow':follow,
                'categoryId':category['id'],'subCategoryId':sub_id,'patternId':pattern_id,'pattern':pattern,
                'memoryTip':tip,'level':'A2-B1','source':'tomeng_host_v1','variant':index,
                'language':'en-US','register':category['register'],'role':'host-to-team' if category['id']=='team' else 'host-to-guest',
                'usageNote':'Câu thực hành cho vận hành căn hộ dịch vụ; xác nhận thông tin thật trước khi báo giá, hứa thời hạn hoặc hướng dẫn an toàn.',
                'tags':['host',category['id'],sub_id,intent]
            }
            phrases.append(phrase)
            patterns[pattern_id]={'id':pattern_id,'name':pattern,'example':en,'categoryId':category['id'],'usage':tip}
            step_records.append({'phraseId':phrase_id,'patternId':pattern_id,'intent':intent,'cue':vi,'turn':turn,'kind':'new'})
        lesson={
            'id':f"host-{category['id']}-{index+1:02d}",'day':0,'title':title,'phraseIds':ids.copy(),
            'candidatePhraseIds':ids.copy(),'reusePhraseIds':[],'newCount':5,'primaryCategoryId':category['id'],
            'primarySubCategoryId':sub_id,'reviewRequired':True,'reviewPhraseIds':[],'durationEstimateMinutes':10,
            'language':'en-US','familyId':category['id'],'scenarioId':f"{category['id']}-{index+1:02d}",
            'scenarioTitle':title,'scenarioGoal':GOALS[category['id']],
            'roleContext':'Bạn đang giao tiếp trong vai trò chủ nhà hoặc nhân viên vận hành căn hộ dịch vụ.',
            'difficulty':'A2-B1','scenarioContext':context,
            'scenarioBridge':'Năm lượt tạo thành mạch xử lý: tiếp nhận, làm rõ, phản hồi, xác nhận phương án và bước tiếp theo.',
            'steps':step_records,'practicePrompt':f"{context} {GOALS[category['id']]} Hãy luyện năm câu theo đúng vai trò và chỉ hứa điều bạn có thể xác nhận.",
            'whyThesePhrases':'Năm câu mới có cùng bối cảnh; lượt sau tiếp nối thông tin vừa thu thập, không phải năm câu rời rạc.'
        }
        host_lessons.append(lesson)
        scenarios.append(lesson)
        cat_phrase_count+=5
        if not any(sub['id']==sub_id for sub in subcategories):
            subcategories.append({'id':sub_id,'categoryId':category['id'],'name':category['flow_names'][flow],'description':GOALS[category['id']],'count':0})
    category_meta.append({'id':category['id'],'name':category['name'],'count':cat_phrase_count,'description':category['description'],'icon':category['icon'],'priority':category['priority']})
    category_queue[category['id']]=scenarios

if host_pointer!=575: raise ValueError(f'Expected 575 Host phrase IDs, allocated {host_pointer}')

# Keep the common Everyday/Reflex scenarios and interleave them with Host tasks.
common_lessons=[dict(lesson) for lesson in CORE_LESSONS if lesson['primaryCategoryId'] in COMMON_CATEGORIES]
category_queue['everyday']=[l for l in common_lessons if l['primaryCategoryId']=='everyday']
category_queue['reflex']=[l for l in common_lessons if l['primaryCategoryId']=='reflex']
ordered=[]
while any(category_queue.values()):
    for category in CATEGORY_DATA:
        queue=category_queue[category['id']]
        if queue: ordered.append(queue.pop(0))
    for core_cat in ('everyday','reflex'):
        queue=category_queue[core_cat]
        if queue: ordered.append(queue.pop(0))
for day,lesson in enumerate(ordered,1):
    lesson['id']=f"day-{day:03d}"; lesson['day']=day
    lesson['reviewRequired']=day>1
    lesson['reviewPhraseIds']=[]
lessons=ordered

for phrase in phrases:
    phrase['day']=next((lesson['day'] for lesson in lessons if phrase['id'] in lesson['candidatePhraseIds']),phrase.get('day',1))
for category in category_meta:
    category['count']=sum(1 for phrase in phrases if phrase['categoryId']==category['id'])
for sub in subcategories:
    sub['count']=sum(1 for phrase in phrases if phrase['subCategoryId']==sub['id'])
patterns_list=list(patterns.values())
meta={'categories':category_meta,'subcategories':subcategories,'lessons':lessons,'patterns':patterns_list,'contentVersion':'host-v1.0.0','trackIds':['everyday','host','mixed']}

HOST.mkdir(parents=True,exist_ok=True)
write(HOST/'phrases.host.v1.json',phrases)
write(HOST/'lessons.host.v1.json',lessons)
write(HOST/'categories.host.v1.json',category_meta)
write(HOST/'subcategories.host.v1.json',subcategories)
write(HOST/'patterns.host.v1.json',patterns_list)
(ROOT/'data.js').write_text('window.SPEAK5_PHRASES = '+json.dumps(phrases,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
(ROOT/'meta.js').write_text('window.TOMENG_META = '+json.dumps(meta,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')

mapping=HOST/'SCENARIO_MAPPING_HOST_V1.csv'
with mapping.open('w',newline='',encoding='utf-8') as handle:
    writer=csv.writer(handle,lineterminator='\n');writer.writerow(['day','lesson_id','category','subcategory','scenario_id','title','candidate_ids','phrase_count'])
    for lesson in lessons: writer.writerow([lesson['day'],lesson['id'],lesson['primaryCategoryId'],lesson.get('primarySubCategoryId',''),lesson['scenarioId'],lesson.get('scenarioTitle',lesson['title']),' '.join(lesson['candidatePhraseIds']),len(lesson['phraseIds'])])

preview=['# TomEng Host — bản xem trước lịch 14 ngày','', 'Bản mẫu tình huống để chủ nhà xem trước; lịch thực tế thích ứng NEW/REUSE theo tiến độ và SRS.','']
for lesson in lessons[:14]:
    preview.extend([f"## Ngày {lesson['day']:03d} · {lesson['scenarioTitle']}",f"**Mục tiêu:** {lesson['scenarioGoal']}",f"**Vai trò:** {lesson['roleContext']}",""])
    for step in lesson['steps']:
        p=next(item for item in phrases if item['id']==step['phraseId'])
        preview.append(f"{step['turn']}. {p['en']} — *{p['vi']}*")
    preview.append('')
(HOST/'PREVIEW_14_DAYS.md').write_text('\n'.join(preview).rstrip()+'\n',encoding='utf-8')

print(f"Built {len(phrases)} phrases ({sum(p['categoryId'] in COMMON_CATEGORIES for p in phrases)} Everyday/Reflex + {sum(p['categoryId'] not in COMMON_CATEGORIES for p in phrases)} Host), {len(lessons)} scenarios, {len(category_meta)} categories.")
