import React, { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Save, AlertTriangle, ShieldCheck } from 'lucide-react'

export default function Settings({ backendUrl }) {
  const [config, setConfig] = useState({
    groq_api_key: '',
    deepgram_api_key: '',
    elevenlabs_api_key: '',
    twilio_account_sid: '',
    twilio_auth_token: '',
    twilio_phone_number: '',
    sms_provider: 'mock',
    llm_model: 'llama-3.3-70b-versatile',
    elevenlabs_voice_id: '21m00Tcm4TlvDq8ikWAM',
    rapidapi_key: '',
    rapidapi_host: 'irctc1.p.rapidapi.com',
    use_real_irctc_api: false,
    use_mock_llm: true,
    use_mock_stt: true,
    use_mock_tts: true,
  })
  
  const [maskedKeys, setMaskedKeys] = useState({})
  const [status, setStatus] = useState({ type: '', message: '' })

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${backendUrl}/dashboard/config`)
      if (res.ok) {
        const data = await res.json()
        setConfig({
          groq_api_key: '',
          deepgram_api_key: '',
          elevenlabs_api_key: '',
          twilio_account_sid: data.twilio_account_sid || '',
          twilio_auth_token: '',
          twilio_phone_number: data.twilio_phone_number || '',
          sms_provider: data.sms_provider || 'mock',
          llm_model: data.llm_model || 'llama-3.3-70b-versatile',
          elevenlabs_voice_id: data.elevenlabs_voice_id || '21m00Tcm4TlvDq8ikWAM',
          rapidapi_key: '',
          rapidapi_host: data.rapidapi_host || 'irctc1.p.rapidapi.com',
          use_real_irctc_api: data.use_real_irctc_api || false,
          use_mock_llm: data.use_mock_llm,
          use_mock_stt: data.use_mock_stt,
          use_mock_tts: data.use_mock_tts,
        })
        setMaskedKeys({
          groq: data.groq_api_key_masked,
          deepgram: data.deepgram_api_key_masked,
          elevenlabs: data.elevenlabs_api_key_masked,
          twilio_auth: data.twilio_auth_token_masked,
          rapidapi: data.rapidapi_key_masked
        })
      }
    } catch (err) {
      console.error("Error fetching configs:", err)
    }
  }

  useEffect(() => {
    fetchConfig()
  }, [backendUrl])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus({ type: 'info', message: 'Saving settings...' })
    try {
      const payload = { ...config }
      
      // If user did not type a new key, don't send anything or send blank to let backend skip
      const res = await fetch(`${backendUrl}/dashboard/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (res.ok) {
        setStatus({ type: 'success', message: 'Configuration saved successfully!' })
        fetchConfig()
      } else {
        setStatus({ type: 'error', message: 'Failed to save configuration.' })
      }
    } catch (err) {
      setStatus({ type: 'error', message: 'Connection to server failed.' })
    }
  }

  return (
    <div className="glass-panel" style={{ padding: '24px', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <SettingsIcon className="spinning-icon" style={{ color: 'var(--color-primary)' }} />
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>System Configuration</h2>
      </div>

      {status.message && (
        <div style={{
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: status.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : status.type === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(99, 102, 241, 0.15)',
          color: status.type === 'success' ? 'var(--color-success)' : status.type === 'error' ? 'var(--color-danger)' : 'var(--color-primary)',
          border: `1px solid ${status.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : status.type === 'error' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`
        }}>
          {status.type === 'success' ? <ShieldCheck size={18} /> : <AlertTriangle size={18} />}
          {status.message}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* LLM settings */}
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            Groq API Key {maskedKeys.groq && <span style={{ color: 'var(--color-success)' }}>({maskedKeys.groq})</span>}
          </label>
          <input
            type="password"
            name="groq_api_key"
            placeholder={maskedKeys.groq ? "Leave empty to keep existing key" : "gsk_..."}
            value={config.groq_api_key}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'rgba(255, 255, 255, 0.03)',
              color: 'var(--text-primary)',
              fontFamily: 'inherit',
              outline: 'none'
            }}
          />
          <div style={{ display: 'flex', alignItems: 'center', marginTop: '6px', marginBottom: '10px' }}>
            <input
              type="checkbox"
              id="use_mock_llm"
              name="use_mock_llm"
              checked={config.use_mock_llm}
              onChange={handleChange}
              style={{ marginRight: '8px' }}
            />
            <label htmlFor="use_mock_llm" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Use Local Regex/Mock Engine (Offline/Free)
            </label>
          </div>
        </div>

        {/* LLM Model Selection */}
        {!config.use_mock_llm && (
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              LLM Conversational Model
            </label>
            <select
              name="llm_model"
              value={config.llm_model}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: '#0f172a',
                color: 'var(--text-primary)',
                fontFamily: 'inherit',
                outline: 'none'
              }}
            >
              <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Humane / Conversational - Recommended)</option>
              <option value="llama-3.1-8b-instant">Llama 3.1 8B (Fast / Lightweight)</option>
              <option value="llama3-70b-8192">Llama 3 70B</option>
            </select>
          </div>
        )}

        {/* STT Settings */}
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            Deepgram API Key {maskedKeys.deepgram && <span style={{ color: 'var(--color-success)' }}>({maskedKeys.deepgram})</span>}
          </label>
          <input
            type="password"
            name="deepgram_api_key"
            placeholder={maskedKeys.deepgram ? "Leave empty to keep existing key" : "Insert Key"}
            value={config.deepgram_api_key}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'rgba(255, 255, 255, 0.03)',
              color: 'var(--text-primary)',
              fontFamily: 'inherit',
              outline: 'none'
            }}
          />
          <div style={{ display: 'flex', alignItems: 'center', marginTop: '6px' }}>
            <input
              type="checkbox"
              id="use_mock_stt"
              name="use_mock_stt"
              checked={config.use_mock_stt}
              onChange={handleChange}
              style={{ marginRight: '8px' }}
            />
            <label htmlFor="use_mock_stt" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Use WebSpeech API in Browser (Free)
            </label>
          </div>
        </div>

        {/* TTS Settings */}
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            ElevenLabs API Key {maskedKeys.elevenlabs && <span style={{ color: 'var(--color-success)' }}>({maskedKeys.elevenlabs})</span>}
          </label>
          <input
            type="password"
            name="elevenlabs_api_key"
            placeholder={maskedKeys.elevenlabs ? "Leave empty to keep existing key" : "Insert Key"}
            value={config.elevenlabs_api_key}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'rgba(255, 255, 255, 0.03)',
              color: 'var(--text-primary)',
              fontFamily: 'inherit',
              outline: 'none'
            }}
          />
          <div style={{ display: 'flex', alignItems: 'center', marginTop: '6px' }}>
            <input
              type="checkbox"
              id="use_mock_tts"
              name="use_mock_tts"
              checked={config.use_mock_tts}
              onChange={handleChange}
              style={{ marginRight: '8px' }}
            />
            <label htmlFor="use_mock_tts" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Use WebSpeech Synthesis in Browser (Free)
            </label>
          </div>
        </div>

        {/* ElevenLabs Voice ID */}
        {!config.use_mock_tts && (
          <div style={{ paddingLeft: '20px', marginTop: '-8px', marginBottom: '4px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              ElevenLabs Voice ID
            </label>
            <input
              type="text"
              name="elevenlabs_voice_id"
              placeholder="e.g., 21m00Tcm4TlvDq8ikWAM"
              value={config.elevenlabs_voice_id}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '8px 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'rgba(255, 255, 255, 0.03)',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
                fontFamily: 'inherit',
                outline: 'none'
              }}
            />
          </div>
        )}

        {/* SMS provider */}
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            SMS Dispatch Provider
          </label>
          <select
            name="sms_provider"
            value={config.sms_provider}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: '#0f172a',
              color: 'var(--text-primary)',
              fontFamily: 'inherit',
              outline: 'none'
            }}
          >
            <option value="mock">Log-Only Simulation (Free)</option>
            <option value="twilio">Twilio SMS Gateway</option>
          </select>
        </div>

        {/* RapidAPI Train API Config */}
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px', marginTop: '4px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '12px', color: 'var(--color-primary)' }}>Indian Railways Live API (RapidAPI)</h3>
          
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
            <input
              type="checkbox"
              id="use_real_irctc_api"
              name="use_real_irctc_api"
              checked={config.use_real_irctc_api}
              onChange={handleChange}
              style={{ marginRight: '8px' }}
            />
            <label htmlFor="use_real_irctc_api" style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>
              Enable Real Train API (RapidAPI)
            </label>
          </div>

          {config.use_real_irctc_api && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingLeft: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  RapidAPI Key {maskedKeys.rapidapi && <span style={{ color: 'var(--color-success)' }}>({maskedKeys.rapidapi})</span>}
                </label>
                <input
                  type="password"
                  name="rapidapi_key"
                  placeholder={maskedKeys.rapidapi ? "Leave empty to keep existing key" : "Enter RapidAPI Key"}
                  value={config.rapidapi_key}
                  onChange={handleChange}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    background: 'rgba(255, 255, 255, 0.03)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem',
                    fontFamily: 'inherit',
                    outline: 'none'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  RapidAPI Host
                </label>
                <input
                  type="text"
                  name="rapidapi_host"
                  placeholder="irctc1.p.rapidapi.com"
                  value={config.rapidapi_host}
                  onChange={handleChange}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    background: 'rgba(255, 255, 255, 0.03)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem',
                    fontFamily: 'inherit',
                    outline: 'none'
                  }}
                />
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          style={{
            marginTop: '10px',
            padding: '12px',
            borderRadius: '8px',
            border: 'none',
            background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)',
            color: 'white',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 4px 14px rgba(99, 102, 241, 0.3)',
            transition: 'var(--transition-smooth)'
          }}
          onMouseEnter={(e) => e.currentTarget.style.opacity = 0.9}
          onMouseLeave={(e) => e.currentTarget.style.opacity = 1}
        >
          <Save size={18} />
          Save Settings
        </button>
      </form>
    </div>
  )
}
