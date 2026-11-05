 Database Design 

 Users

 id
 name
 email
 hashed_password
 phone
 age
 gender
 address line 1
 address line 2
 district
 state
 pincode
 seating_capacity
 role
 is_active
 created_At
 updated_at


Vehicles 

id – Primary key

seller_id – Foreign key to users.id

brand

model

variant

registration_number – Unique

manufacturing_year

fuel_type

transmission

kilometers_driven

ownership_count

expected_price

description

status

created_at

updated_at


Vehicles Inspection 

id – Primary key

vehicle_id – Foreign key to vehicles.id

consultant_id – Nullable foreign key to users.id

condition

engine_condition

exterior_condition

interior_condition

accident_history

estimated_market_value

inspection_notes

inspection_date

status


Vehicle Listing 

id – Primary key

vehicle_id – Unique foreign key to vehicles.id

listed_price

listing_description

status

listed_at

updated_at


Resale Transaction 

id – Primary key

listing_id – Foreign key to resale_listings.id

buyer_id – Foreign key to users.id

seller_id – Foreign key to users.id

consultant_id – foreign key to users.id

final_price

status

delivery_date 

created_at

updated_at




{
  "name": "Vishal M",
  "email": "visowmani.123@gmail.com",
  "password": "Vishal@1205",
  "phone": "6379543139",
  "age": 21,
  "gender": "male",
  "address_line_1": "2/201 B, Annapoorani Nagar",
  "address_line_2": "Theethipalayam",
  "district": "Coimbatore",
  "state": "Tamilnadu",
  "pincode": "641010"
}   


admin@example.com
AdminPassword@123

visowmani.123@gmail.com
Vishal@1205

sanjaysammathew05@gmail.com
Sanjay@1205

            "brand": "Maruti Suzuki",
            "model": "Swift",
            "variant": "ZXI Plus",
            "registration_number": "TESTCON01",
            "manufacturing_year": 2022,
            "fuel_type": "petrol",
            "transmission": "manual",
            "kilometers_driven": 18000,
            "ownership_count": 1,
            "expected_price": 650000.00,
            "seating_capacity": 5,
            "description": "TESTCON Single owner well maintained car"
