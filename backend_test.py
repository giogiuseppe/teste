import requests
import unittest
from datetime import datetime, timedelta
import json
import sys

# Use the public endpoint from the frontend .env file
API_URL = "https://b5562165-2bb5-4b81-95c4-0712ff297adc.preview.emergentagent.com"

class BarBookingAPITest(unittest.TestCase):
    def setUp(self):
        # Generate a unique date for testing (tomorrow)
        tomorrow = datetime.now() + timedelta(days=1)
        self.test_date = tomorrow.strftime("%Y-%m-%d")
        self.test_time = "19:00"  # 7 PM
        self.test_party_size = 4
        
        # For storing created booking ID
        self.booking_id = None

    def test_01_health_check(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing health check endpoint...")
        response = requests.get(f"{API_URL}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print("✅ Health check endpoint is working")

    def test_02_get_tables(self):
        """Test getting all tables"""
        print("\n🔍 Testing get tables endpoint...")
        response = requests.get(f"{API_URL}/api/tables")
        self.assertEqual(response.status_code, 200)
        tables = response.json()
        self.assertIsInstance(tables, list)
        self.assertGreaterEqual(len(tables), 1)
        
        # Verify table structure
        first_table = tables[0]
        self.assertIn("id", first_table)
        self.assertIn("name", first_table)
        self.assertIn("capacity", first_table)
        self.assertIn("location", first_table)
        print(f"✅ Get tables endpoint returned {len(tables)} tables")

    def test_03_check_availability(self):
        """Test checking table availability"""
        print("\n🔍 Testing check availability endpoint...")
        payload = {
            "booking_date": self.test_date,
            "booking_time": self.test_time,
            "party_size": self.test_party_size
        }
        
        response = requests.post(
            f"{API_URL}/api/check-availability",
            json=payload
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("available_tables", data)
        self.assertIn("booking_date", data)
        self.assertIn("booking_time", data)
        self.assertIn("party_size", data)
        
        # Store a table ID for booking test if available
        if data["available_tables"]:
            self.table_id = data["available_tables"][0]["id"]
            self.table_name = data["available_tables"][0]["name"]
            print(f"✅ Check availability endpoint returned {len(data['available_tables'])} available tables")
        else:
            print("⚠️ No tables available for testing booking creation")
            self.table_id = None

    def test_04_create_booking(self):
        """Test creating a booking"""
        # Skip if no table is available
        if not hasattr(self, 'table_id') or not self.table_id:
            self.skipTest("No available table for booking")
            
        print("\n🔍 Testing create booking endpoint...")
        payload = {
            "table_id": self.table_id,
            "customer_name": "Test Customer",
            "customer_phone": "123-456-7890",
            "party_size": self.test_party_size,
            "booking_date": self.test_date,
            "booking_time": self.test_time,
            "special_requests": "Test booking, please ignore"
        }
        
        response = requests.post(
            f"{API_URL}/api/bookings",
            json=payload
        )
        self.assertEqual(response.status_code, 200)
        booking = response.json()
        
        # Verify booking structure
        self.assertIn("id", booking)
        self.assertEqual(booking["table_id"], self.table_id)
        self.assertEqual(booking["table_name"], self.table_name)
        self.assertEqual(booking["customer_name"], "Test Customer")
        self.assertEqual(booking["customer_phone"], "123-456-7890")
        self.assertEqual(booking["party_size"], self.test_party_size)
        self.assertEqual(booking["booking_date"], self.test_date)
        self.assertEqual(booking["booking_time"], self.test_time)
        
        # Store booking ID for later tests
        self.booking_id = booking["id"]
        print(f"✅ Create booking endpoint created booking with ID: {self.booking_id}")

    def test_05_verify_double_booking_prevention(self):
        """Test that double booking is prevented"""
        # Skip if no booking was created
        if not hasattr(self, 'booking_id') or not self.booking_id:
            self.skipTest("No booking created to test double booking prevention")
            
        print("\n🔍 Testing double booking prevention...")
        payload = {
            "table_id": self.table_id,
            "customer_name": "Another Customer",
            "customer_phone": "987-654-3210",
            "party_size": self.test_party_size,
            "booking_date": self.test_date,
            "booking_time": self.test_time,
            "special_requests": "This should fail"
        }
        
        response = requests.post(
            f"{API_URL}/api/bookings",
            json=payload
        )
        self.assertEqual(response.status_code, 400)
        error = response.json()
        self.assertIn("detail", error)
        print("✅ Double booking prevention is working")

    def test_06_get_bookings(self):
        """Test getting all bookings"""
        print("\n🔍 Testing get bookings endpoint...")
        response = requests.get(f"{API_URL}/api/bookings")
        self.assertEqual(response.status_code, 200)
        bookings = response.json()
        self.assertIsInstance(bookings, list)
        print(f"✅ Get bookings endpoint returned {len(bookings)} bookings")

    def test_07_get_bookings_by_date(self):
        """Test getting bookings by date"""
        print("\n🔍 Testing get bookings by date endpoint...")
        response = requests.get(f"{API_URL}/api/bookings?date={self.test_date}")
        self.assertEqual(response.status_code, 200)
        bookings = response.json()
        self.assertIsInstance(bookings, list)
        
        # If we created a booking, verify it's in the results
        if hasattr(self, 'booking_id') and self.booking_id:
            booking_ids = [booking["id"] for booking in bookings]
            self.assertIn(self.booking_id, booking_ids)
        
        print(f"✅ Get bookings by date endpoint returned {len(bookings)} bookings for date {self.test_date}")

    def test_08_get_booking_by_id(self):
        """Test getting a specific booking by ID"""
        # Skip if no booking was created
        if not hasattr(self, 'booking_id') or not self.booking_id:
            self.skipTest("No booking created to test get booking by ID")
            
        print("\n🔍 Testing get booking by ID endpoint...")
        response = requests.get(f"{API_URL}/api/bookings/{self.booking_id}")
        self.assertEqual(response.status_code, 200)
        booking = response.json()
        
        self.assertEqual(booking["id"], self.booking_id)
        self.assertEqual(booking["table_id"], self.table_id)
        self.assertEqual(booking["customer_name"], "Test Customer")
        print(f"✅ Get booking by ID endpoint returned the correct booking")

    def test_09_verify_availability_after_booking(self):
        """Test that booked tables are no longer available"""
        # Skip if no booking was created
        if not hasattr(self, 'booking_id') or not self.booking_id:
            self.skipTest("No booking created to test availability after booking")
            
        print("\n🔍 Testing availability after booking...")
        payload = {
            "booking_date": self.test_date,
            "booking_time": self.test_time,
            "party_size": self.test_party_size
        }
        
        response = requests.post(
            f"{API_URL}/api/check-availability",
            json=payload
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that our booked table is not in available tables
        available_table_ids = [table["id"] for table in data["available_tables"]]
        self.assertNotIn(self.table_id, available_table_ids)
        print("✅ Booked table is correctly marked as unavailable")

def run_tests():
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(BarBookingAPITest)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return the number of failures and errors
    return len(result.failures) + len(result.errors)

if __name__ == "__main__":
    print("🧪 Running Bar Booking API Tests 🧪")
    exit_code = run_tests()
    sys.exit(exit_code)