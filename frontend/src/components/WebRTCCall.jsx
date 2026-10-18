import React, { useState, useEffect, useRef } from 'react'
import { Phone, PhoneOff, Mic, MicOff, Volume2, Activity } from 'lucide-react'
import AudioWave from './AudioWave'
import useVoiceCall from './useVoiceCall'

const getStationCode = (name) => {
  if (!name) return '';
  const clean = name.trim().toLowerCase();
  const map = {
    'delhi': 'NDLS',
    'new delhi': 'NDLS',
    'chandigarh': 'CDG',
    'mumbai': 'MMCT',
    'mumbai central': 'MMCT',
    'bhopal': 'BPL',
    'varanasi': 'BSB',
    'lucknow': 'LKO',
    'patna': 'PNBE',
    'bangalore': 'SBC',
    'chennai': 'MAS',
    'pune': 'PUNE',
    'ernakulam': 'ERS',
    'patiala': 'PTA',
    'nizar': 'NIZAR',
    'ahmedabad': 'ADI'
  };
  return map[clean] || name.slice(0, 4).toUpperCase();
};

const formatTicketDate = (dateStr) => {
  if (!dateStr) return 'Tomorrow';
  try {
    if (dateStr.toLowerCase() === 'tomorrow') {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      return tomorrow.toLocaleDateString('en-US', { day: 'numeric', month: 'short', weekday: 'long' });
    }
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      const day = date.getDate();
      const month = date.toLocaleDateString('en-US', { month: 'short' });
      const weekday = date.toLocaleDateString('en-US', { weekday: 'long' });
      return `${day} ${month} ${weekday}`;
    }
    return dateStr;
  } catch (e) {
    return dateStr;
  }
};

const getClassName = (code) => {
  const map = {
    'SL': 'Sleeper (SL)',
    '3A': 'AC 3 Tier (3A)',
    '3E': 'AC 3 Tier Economy (3E)',
    '2A': 'AC 2 Tier (2A)',
    '1A': 'AC First Class (1A)',
    'CC': 'AC Chair Car (CC)',
    'EC': 'Exec. Chair Car (EC)',
    '2S': 'Second Sitting (2S)'
  };
  return map[code.toUpperCase()] || code;
};

const getStableTicketNo = (pnr) => {
  if (!pnr) return 'TQC988093532';
  let hash = 0;
  for (let i = 0; i < pnr.length; i++) {
    hash = pnr.charCodeAt(i) + ((hash << 5) - hash);
  }
  const num = Math.abs(hash % 9000000000) + 1000000000;
  return `TQC${num}`;
};

export default function WebRTCCall({ backendUrl, onCallStateChange }) {
  const { inCall, callId, currentState, transcript, slots, isMuted, agentSpeaking, error,
    startCall, endCall, toggleMute, selectTrain } = useVoiceCall(backendUrl, onCallStateChange)

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {error && <div role="alert" style={{ color: 'var(--color-danger)', padding: '12px', border: '1px solid currentColor', borderRadius: '8px' }}>{error}</div>}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Volume2 style={{ color: 'var(--color-primary)' }} />
          Voice Agent Terminal
        </h2>
        {inCall && (
          <span style={{
            background: 'rgba(99, 102, 241, 0.15)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: 'var(--color-primary)',
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Activity className="spinning-icon" size={12} />
            Live ID: {callId}
          </span>
        )}
      </div>

      <div style={{
        background: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        height: '450px',
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        {transcript.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', textAlign: 'center', gap: '8px' }}>
            <Phone size={36} style={{ strokeWidth: 1 }} />
            <p style={{ fontSize: '0.85rem' }}>No active call. Dial in below to speak to the booking agent.</p>
          </div>
        ) : (
          transcript.map((t, idx) => {
            const isUser = t.sender === 'user';

            // Check if there is an execution result for booking or PNR check
            let bookingData = null;
            if (t.lastActionResult) {
              if (t.lastActionResult.pnr && t.lastActionResult.train_no) {
                bookingData = t.lastActionResult;
              } else if (t.lastActionResult.booking) {
                bookingData = t.lastActionResult.booking;
              }
            }

            const hasTrains = t.availableTrains && t.availableTrains.length > 0;

            return (
              <div key={idx} style={{
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                width: '100%',
                maxWidth: '85%',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{
                  alignSelf: isUser ? 'flex-end' : 'flex-start',
                  background: isUser ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${isUser ? 'rgba(99, 102, 241, 0.25)' : 'var(--border-color)'}`,
                  padding: '10px 14px',
                  borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                  fontSize: '0.9rem',
                  lineHeight: 1.4,
                  width: 'fit-content',
                  flexShrink: 0
                }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'capitalize' }}>
                    {t.sender}
                  </div>
                  <div>{t.text}</div>
                </div>

                {/* 1. Beautiful ticket card rendering if booking information is available */}
                {bookingData && (() => {
                  const slotsSource = t.slots?.source || slots.source || 'Delhi';
                  const slotsDestination = t.slots?.destination || slots.destination || 'Chandigarh';
                  const slotsDate = t.slots?.date || slots.date || 'tomorrow';

                  const matchedTrain = t.availableTrains?.find(train => train.no === bookingData.train_no) || {};
                  const depTime = bookingData.dep || matchedTrain.dep || '06:00 AM';
                  const arrTime = bookingData.arr || matchedTrain.arr || '12:00 PM';
                  const duration = bookingData.duration || matchedTrain.duration || '06.00';

                  return (
                    <div style={{
                      alignSelf: 'flex-start',
                      width: '290px',
                      borderRadius: '16px',
                      overflow: 'hidden',
                      flexShrink: 0,
                      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      fontFamily: 'system-ui, -apple-system, sans-serif',
                      marginBottom: '10px'
                    }}>
                      {/* Top Section - Blue Block */}
                      <div style={{
                        background: '#6366f1',
                        padding: '16px',
                        color: 'white',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px'
                      }}>
                        {/* Station Timeline */}
                        <div style={{ position: 'relative', paddingLeft: '24px' }}>
                          {/* Dotted Line */}
                          <div style={{
                            position: 'absolute',
                            left: '7px',
                            top: '12px',
                            bottom: '12px',
                            borderLeft: '2px dotted rgba(255, 255, 255, 0.5)'
                          }} />

                          {/* Source Station */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <span style={{ fontSize: '14px', position: 'relative', zIndex: 2 }}>🏢</span>
                            <div>
                              <div style={{ fontSize: '1.05rem', fontWeight: 'bold', lineHeight: '1.2' }}>
                                {bookingData.src || slotsSource}
                              </div>
                              <div style={{ fontSize: '0.75rem', opacity: 0.8, textTransform: 'uppercase' }}>
                                {getStationCode(bookingData.src || slotsSource)}
                              </div>
                            </div>
                          </div>

                          {/* Destination Station */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '14px', position: 'relative', zIndex: 2 }}>🏢</span>
                            <div>
                              <div style={{ fontSize: '1.05rem', fontWeight: 'bold', lineHeight: '1.2' }}>
                                {bookingData.dst || slotsDestination}
                              </div>
                              <div style={{ fontSize: '0.75rem', opacity: 0.8, textTransform: 'uppercase' }}>
                                {getStationCode(bookingData.dst || slotsDestination)}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Divider */}
                        <div style={{ height: '1px', background: 'rgba(255, 255, 255, 0.25)' }} />

                        {/* Timings */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                          <span style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                            {depTime} - {arrTime}
                          </span>
                        </div>

                        {/* Duration */}
                        <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                          Duration: {duration}
                        </div>

                        {/* Date */}
                        <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                          {formatTicketDate(bookingData.date || slotsDate)}
                        </div>

                        {/* Train Name/Number */}
                        <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                          {bookingData.train_name || 'Express'} ({bookingData.train_no || '12002'})
                        </div>

                        {/* Class */}
                        <div style={{ fontSize: '0.85rem', fontWeight: '500' }}>
                          {getClassName(bookingData.class_code || 'CC')}
                        </div>
                      </div>

                      {/* Bottom Section - White Block */}
                      <div style={{
                        background: '#ffffff',
                        padding: '16px',
                        color: '#1f2937',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px',
                        fontSize: '0.85rem'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ color: '#4b5563' }}>Seat No</span>
                          <strong style={{ color: '#111827' }}>
                            {bookingData.coach || 'B1'} - {bookingData.berth || '14'} ({bookingData.status || 'CNF'})
                          </strong>
                        </div>

                        <div style={{ borderTop: '1px dashed #d1d5db', margin: '4px 0' }} />

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ color: '#4b5563' }}>Ticket No</span>
                          <strong style={{ color: '#111827' }}>{getStableTicketNo(bookingData.pnr)}</strong>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ color: '#4b5563' }}>PNR</span>
                          <strong style={{ color: '#1d4ed8' }}>{bookingData.pnr || 'G45325329'}</strong>
                        </div>

                        <div style={{ borderTop: '1px dashed #d1d5db', margin: '4px 0' }} />

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
                          <span style={{ color: '#111827', fontWeight: 'bold' }}>Fare</span>
                          <strong style={{ fontSize: '1.05rem', color: '#111827' }}>
                            ₹ {parseFloat(bookingData.price || 850).toFixed(2)}
                          </strong>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* 2. Available trains list card rendering */}
                {hasTrains && (
                  <div style={{
                    alignSelf: 'flex-start',
                    width: '100%',
                    display: 'flex',
                    flexDirection: 'row',
                    gap: '16px',
                    overflowX: 'auto',
                    overflowY: 'hidden',
                    padding: '8px 4px',
                    borderRadius: '8px',
                    marginBottom: '10px',
                    flexShrink: 0
                  }}>
                    {t.availableTrains.flatMap((train) => {
                      const classes = (train.classes || []).map(code => [code, train.class_details?.[code] || { status: 'UNKNOWN', seats: null, price: null }]);
                      if (classes.length === 0) {
                        return [];
                      }
                      return classes.map(([classCode, classInfo]) => ({
                        train,
                        classCode,
                        classInfo
                      }));
                    }).slice(0, 4).map(({ train, classCode, classInfo }, idx) => {
                      const slotsSource = t.slots?.source || slots.source || 'Delhi';
                      const slotsDestination = t.slots?.destination || slots.destination || 'Chandigarh';
                      const slotsDate = t.slots?.date || slots.date || 'tomorrow';

                      const depTime = train.dep || 'Unavailable';
                      const arrTime = train.arr || 'Unavailable';
                      const duration = train.duration || 'Unavailable';

                      return (
                        <div key={idx} 
                          onClick={() => selectTrain(train, classCode)}
                          className="clickable-card"
                          style={{
                            width: '290px',
                            minWidth: '290px',
                            borderRadius: '16px',
                            overflow: 'hidden',
                            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
                            border: '1px solid rgba(255, 255, 255, 0.08)',
                            fontFamily: 'system-ui, -apple-system, sans-serif',
                            background: '#ffffff',
                            flexShrink: 0,
                            cursor: 'pointer'
                          }}>
                          {/* Top Section - Blue Block */}
                          <div style={{
                            background: '#6366f1',
                            padding: '16px',
                            color: 'white',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px'
                          }}>
                            {/* Station Timeline */}
                            <div style={{ position: 'relative', paddingLeft: '24px' }}>
                              {/* Dotted Line */}
                              <div style={{
                                position: 'absolute',
                                left: '7px',
                                top: '12px',
                                bottom: '12px',
                                borderLeft: '2px dotted rgba(255, 255, 255, 0.5)'
                              }} />

                              {/* Source Station */}
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                <span style={{ fontSize: '14px', position: 'relative', zIndex: 2 }}>🏢</span>
                                <div>
                                  <div style={{ fontSize: '1.05rem', fontWeight: 'bold', lineHeight: '1.2' }}>
                                    {train.src || slotsSource}
                                  </div>
                                  <div style={{ fontSize: '0.75rem', opacity: 0.8, textTransform: 'uppercase' }}>
                                    {getStationCode(train.src || slotsSource)}
                                  </div>
                                </div>
                              </div>

                              {/* Destination Station */}
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '14px', position: 'relative', zIndex: 2 }}>🏢</span>
                                <div>
                                  <div style={{ fontSize: '1.05rem', fontWeight: 'bold', lineHeight: '1.2' }}>
                                    {train.dst || slotsDestination}
                                  </div>
                                  <div style={{ fontSize: '0.75rem', opacity: 0.8, textTransform: 'uppercase' }}>
                                    {getStationCode(train.dst || slotsDestination)}
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Divider */}
                            <div style={{ height: '1px', background: 'rgba(255, 255, 255, 0.25)' }} />

                            {/* Timings */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                              <span style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                                {depTime} - {arrTime}
                              </span>
                            </div>

                            {/* Duration */}
                            <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                              Duration: {duration}
                            </div>

                            {/* Date */}
                            <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                              {formatTicketDate(slotsDate)}
                            </div>

                            {/* Train Operator */}
                            <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                              {train.name || 'Express'} ({train.no || '12002'})
                            </div>

                            {/* Class */}
                            <div style={{ fontSize: '0.85rem', fontWeight: '500' }}>
                              {getClassName(classCode)}
                            </div>
                          </div>

                          {/* Bottom Section - White Block */}
                          <div style={{
                            background: '#ffffff',
                            padding: '16px',
                            color: '#1f2937',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px',
                            fontSize: '0.85rem'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ color: '#4b5563' }}>Seat Status</span>
                              <strong style={{ color: classInfo.seats > 0 ? '#10b981' : '#ef4444' }}>
                                {classInfo.status || 'UNKNOWN'} {classInfo.seats != null ? `(${classInfo.seats})` : ''}
                              </strong>
                            </div>

                            <div style={{ borderTop: '1px dashed #d1d5db', margin: '4px 0' }} />

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ color: '#4b5563' }}>Train No</span>
                              <strong style={{ color: '#111827' }}>{train.no}</strong>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ color: '#4b5563' }}>PNR Status</span>
                              <strong style={{ color: '#1d4ed8' }}>SEARCH-ACTIVE</strong>
                            </div>

                            <div style={{ borderTop: '1px dashed #d1d5db', margin: '4px 0' }} />

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
                              <span style={{ color: '#111827', fontWeight: 'bold' }}>Fare</span>
                              <strong style={{ fontSize: '1.05rem', color: '#111827' }}>
                                {classInfo.price != null ? `₹ ${Number(classInfo.price).toFixed(2)}` : 'Fare unavailable'}
                              </strong>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Visualizer wave while agent or user speaking */}
      <div style={{ height: '60px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <AudioWave isActive={inCall} isSilent={agentSpeaking || isMuted} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
        {!inCall ? (
          <button
            onClick={startCall}
            style={{
              padding: '12px 28px',
              borderRadius: '24px',
              border: 'none',
              background: 'linear-gradient(135deg, var(--color-success) 0%, #059669 100%)',
              color: 'white',
              fontWeight: 600,
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(16, 185, 129, 0.35)',
              transition: 'var(--transition-smooth)'
            }}
          >
            <Phone size={18} />
            Start Voice Call
          </button>
        ) : (
          <>
            <button
              onClick={toggleMute}
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                border: '1px solid var(--border-color)',
                background: isMuted ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                color: isMuted ? 'var(--color-danger)' : 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'var(--transition-smooth)'
              }}
            >
              {isMuted ? <MicOff size={20} /> : <Mic size={20} />}
            </button>

            <button
              onClick={endCall}
              style={{
                padding: '12px 28px',
                borderRadius: '24px',
                border: 'none',
                background: 'linear-gradient(135deg, var(--color-danger) 0%, #b91c1c 100%)',
                color: 'white',
                fontWeight: 600,
                fontSize: '0.95rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                boxShadow: '0 4px 16px rgba(239, 68, 68, 0.35)',
                transition: 'var(--transition-smooth)'
              }}
            >
              <PhoneOff size={18} />
              End Call
            </button>
          </>
        )}
      </div>

      <div style={{
        textAlign: 'center',
        fontSize: '0.75rem',
        color: 'var(--text-secondary)',
        borderTop: '1px solid var(--border-color)',
        paddingTop: '12px',
        display: 'flex',
        justifyContent: 'space-around'
      }}>
        <span>Status: <strong style={{ color: inCall ? 'var(--color-success)' : 'var(--text-muted)' }}>{currentState}</strong></span>
        <span>Mode: <strong>{"Live voice"}</strong></span>
      </div>
    </div>
  )
}
