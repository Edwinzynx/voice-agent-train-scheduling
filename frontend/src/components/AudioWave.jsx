import React from 'react'
import './AudioWave.css'

export default function AudioWave({ isSilent, isActive }) {
  if (!isActive) return null;
  
  return (
    <div className={`wave-container ${isSilent ? 'silent' : ''}`}>
      <div className="wave-bar" style={{ height: '30%' }}></div>
      <div className="wave-bar" style={{ height: '70%' }}></div>
      <div className="wave-bar" style={{ height: '50%' }}></div>
      <div className="wave-bar" style={{ height: '90%' }}></div>
      <div className="wave-bar" style={{ height: '40%' }}></div>
      <div className="wave-bar" style={{ height: '80%' }}></div>
      <div className="wave-bar" style={{ height: '60%' }}></div>
      <div className="wave-bar" style={{ height: '30%' }}></div>
    </div>
  )
}
