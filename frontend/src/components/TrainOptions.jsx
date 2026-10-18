import React from 'react'
import { ArrowRight } from 'lucide-react'

function displayDate(value) {
  if (!value) return 'Date not selected'
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T12:00:00+05:30`) : null
  return date && !Number.isNaN(date.getTime())
    ? date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' }) : value
}

export default function TrainOptions({ trains, slots, disabled, onSelect }) {
  return <div className="train-options" aria-label="Train options">
    <span className="train-options-title">{trains.length} trains · Choose a class within a train to check seats</span>
    {trains.map((train, index) => <article className="train-option" key={train.no} aria-label={`${train.name || train.no} (${train.no})`}>
      <span className="train-option-heading">Train {index + 1} · {train.no}</span>
      <strong>{train.name || train.no}</strong>
      <span>{train.src || slots?.source || 'Origin unavailable'} → {train.dst || slots?.destination || 'Destination unavailable'}</span>
      <span>{displayDate(slots?.date)} · {train.dep || 'Time unavailable'} → {train.arr || 'Time unavailable'}</span>
      <div className="train-classes" aria-label="Available classes">
        {(train.classes || []).map(classCode => {
          const info = train.class_details?.[classCode] || {}
          return <button className="train-class" key={classCode} disabled={disabled}
            aria-label={`Select ${classCode} on ${train.name || train.no} (${train.no})`}
            onClick={() => onSelect(train, classCode)}>
            <strong>{classCode}</strong>
            <span className="train-availability">{info.status || 'Availability not returned'}{info.seats != null ? ` · ${info.seats} seats` : ''}{info.price != null ? ` · ₹${info.price}` : ''}</span>
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        })}
        {!train.classes?.length && <span className="train-availability">Class information was not returned for this train.</span>}
      </div>
    </article>)}
  </div>
}
