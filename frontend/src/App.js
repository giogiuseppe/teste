import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentStep, setCurrentStep] = useState('date');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [partySize, setPartySize] = useState(2);
  const [availableTables, setAvailableTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [specialRequests, setSpecialRequests] = useState('');
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Time slots from 5 PM to midnight
  const timeSlots = [
    '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
  ];

  // Get today's date in YYYY-MM-DD format
  const getTodayDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  // Get formatted date for display
  const getFormattedDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Get formatted time for display
  const getFormattedTime = (timeString) => {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  // Check availability
  const checkAvailability = async () => {
    if (!selectedDate || !selectedTime || !partySize) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/check-availability`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          booking_date: selectedDate,
          booking_time: selectedTime,
          party_size: partySize
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to check availability');
      }

      const data = await response.json();
      setAvailableTables(data.available_tables);
      setCurrentStep('tables');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Create booking
  const createBooking = async () => {
    if (!selectedTable || !customerName || !customerPhone) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          table_id: selectedTable.id,
          customer_name: customerName,
          customer_phone: customerPhone,
          party_size: partySize,
          booking_date: selectedDate,
          booking_time: selectedTime,
          special_requests: specialRequests
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create booking');
      }

      const bookingData = await response.json();
      setBooking(bookingData);
      setCurrentStep('confirmation');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Reset to start
  const resetBooking = () => {
    setCurrentStep('date');
    setSelectedDate('');
    setSelectedTime('');
    setPartySize(2);
    setAvailableTables([]);
    setSelectedTable(null);
    setCustomerName('');
    setCustomerPhone('');
    setSpecialRequests('');
    setBooking(null);
    setError('');
  };

  // Render date selection step
  const renderDateStep = () => (
    <div className="step-container">
      <h2 className="step-title">Select Date & Time</h2>
      
      <div className="form-group">
        <label className="form-label">Date</label>
        <input
          type="date"
          className="form-input"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          min={getTodayDate()}
        />
      </div>

      <div className="form-group">
        <label className="form-label">Time</label>
        <div className="time-slots">
          {timeSlots.map(time => (
            <button
              key={time}
              className={`time-slot ${selectedTime === time ? 'selected' : ''}`}
              onClick={() => setSelectedTime(time)}
            >
              {getFormattedTime(time)}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Party Size</label>
        <div className="party-size-controls">
          <button
            className="party-size-btn"
            onClick={() => setPartySize(Math.max(1, partySize - 1))}
          >
            -
          </button>
          <span className="party-size-display">{partySize}</span>
          <button
            className="party-size-btn"
            onClick={() => setPartySize(Math.min(10, partySize + 1))}
          >
            +
          </button>
        </div>
      </div>

      <button
        className="next-btn"
        onClick={checkAvailability}
        disabled={!selectedDate || !selectedTime || loading}
      >
        {loading ? 'Checking...' : 'Check Availability'}
      </button>
    </div>
  );

  // Render table selection step
  const renderTablesStep = () => (
    <div className="step-container">
      <h2 className="step-title">Select Table</h2>
      
      <div className="booking-summary">
        <p><strong>Date:</strong> {getFormattedDate(selectedDate)}</p>
        <p><strong>Time:</strong> {getFormattedTime(selectedTime)}</p>
        <p><strong>Party Size:</strong> {partySize} people</p>
      </div>

      {availableTables.length === 0 ? (
        <div className="no-tables">
          <p>No tables available for this time slot.</p>
          <button className="back-btn" onClick={() => setCurrentStep('date')}>
            Try Different Time
          </button>
        </div>
      ) : (
        <>
          <div className="tables-grid">
            {availableTables.map(table => (
              <div
                key={table.id}
                className={`table-card ${selectedTable?.id === table.id ? 'selected' : ''}`}
                onClick={() => setSelectedTable(table)}
              >
                <h3>{table.name}</h3>
                <p>Capacity: {table.capacity} people</p>
                <p>Location: {table.location}</p>
              </div>
            ))}
          </div>

          <div className="step-actions">
            <button className="back-btn" onClick={() => setCurrentStep('date')}>
              Back
            </button>
            <button
              className="next-btn"
              onClick={() => setCurrentStep('details')}
              disabled={!selectedTable}
            >
              Continue
            </button>
          </div>
        </>
      )}
    </div>
  );

  // Render customer details step
  const renderDetailsStep = () => (
    <div className="step-container">
      <h2 className="step-title">Your Details</h2>
      
      <div className="booking-summary">
        <p><strong>Table:</strong> {selectedTable?.name}</p>
        <p><strong>Date:</strong> {getFormattedDate(selectedDate)}</p>
        <p><strong>Time:</strong> {getFormattedTime(selectedTime)}</p>
        <p><strong>Party Size:</strong> {partySize} people</p>
      </div>

      <div className="form-group">
        <label className="form-label">Your Name *</label>
        <input
          type="text"
          className="form-input"
          value={customerName}
          onChange={(e) => setCustomerName(e.target.value)}
          placeholder="Enter your name"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Phone Number *</label>
        <input
          type="tel"
          className="form-input"
          value={customerPhone}
          onChange={(e) => setCustomerPhone(e.target.value)}
          placeholder="Enter your phone number"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Special Requests</label>
        <textarea
          className="form-input"
          value={specialRequests}
          onChange={(e) => setSpecialRequests(e.target.value)}
          placeholder="Any special requests or dietary requirements?"
          rows="3"
        />
      </div>

      <div className="step-actions">
        <button className="back-btn" onClick={() => setCurrentStep('tables')}>
          Back
        </button>
        <button
          className="next-btn"
          onClick={createBooking}
          disabled={!customerName || !customerPhone || loading}
        >
          {loading ? 'Booking...' : 'Confirm Booking'}
        </button>
      </div>
    </div>
  );

  // Render confirmation step
  const renderConfirmationStep = () => (
    <div className="step-container">
      <div className="confirmation-success">
        <div className="success-icon">✅</div>
        <h2>Booking Confirmed!</h2>
        <p>Your table has been successfully reserved.</p>
      </div>

      <div className="booking-details">
        <h3>Booking Details</h3>
        <div className="detail-row">
          <span>Booking ID:</span>
          <span>{booking?.id}</span>
        </div>
        <div className="detail-row">
          <span>Table:</span>
          <span>{booking?.table_name}</span>
        </div>
        <div className="detail-row">
          <span>Date:</span>
          <span>{getFormattedDate(booking?.booking_date)}</span>
        </div>
        <div className="detail-row">
          <span>Time:</span>
          <span>{getFormattedTime(booking?.booking_time)}</span>
        </div>
        <div className="detail-row">
          <span>Party Size:</span>
          <span>{booking?.party_size} people</span>
        </div>
        <div className="detail-row">
          <span>Name:</span>
          <span>{booking?.customer_name}</span>
        </div>
        <div className="detail-row">
          <span>Phone:</span>
          <span>{booking?.customer_phone}</span>
        </div>
        {booking?.special_requests && (
          <div className="detail-row">
            <span>Special Requests:</span>
            <span>{booking?.special_requests}</span>
          </div>
        )}
      </div>

      <div className="confirmation-actions">
        <button className="primary-btn" onClick={resetBooking}>
          Book Another Table
        </button>
        <button className="secondary-btn" onClick={() => window.location.href = `tel:${booking?.customer_phone}`}>
          Call Restaurant
        </button>
      </div>
    </div>
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>🍺 Reserve Your Table</h1>
        <p>Book your perfect spot at our bar</p>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-message">
            <span>❌ {error}</span>
            <button onClick={() => setError('')}>✕</button>
          </div>
        )}

        {currentStep === 'date' && renderDateStep()}
        {currentStep === 'tables' && renderTablesStep()}
        {currentStep === 'details' && renderDetailsStep()}
        {currentStep === 'confirmation' && renderConfirmationStep()}
      </main>

      <footer className="app-footer">
        <p>&copy; 2025 Bar Table Booking System</p>
      </footer>
    </div>
  );
}

export default App;