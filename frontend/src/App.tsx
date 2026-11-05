import { useState } from 'react'

export default function App() {
  const [message, setMessage] = useState('')

  function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const password = String(form.get('password') ?? '')
    const confirmPassword = String(form.get('confirmPassword') ?? '')

    if (password !== confirmPassword) {
      setMessage('Those passwords do not match. Please try again.')
      return
    }

    setMessage('Your details look good. Account creation will be available when authentication is connected.')
  }

  return (
    <main className="signup-page">

      <section className="signup-main" aria-labelledby="signup-title">
        <div className="signup-content">
          <h2 id="signup-title">Create your account</h2><br />

          <form className="signup-form" onSubmit={handleSubmit}>
            <label htmlFor="displayName">Username</label>
            <input id="displayName" name="displayName" type="text" placeholder="Who are you?" autoComplete="nickname" required minLength={2} maxLength={30} />

            <label htmlFor="email">Email address</label>
            <input id="email" name="email" type="email" placeholder="you@example.com" autoComplete="email" required />

            <label htmlFor="password">Password</label>
            <input id="password" name="password" type="password" placeholder="At least 8 characters" autoComplete="new-password" required minLength={8} />

            <label htmlFor="confirmPassword">Confirm password</label>
            <input id="confirmPassword" name="confirmPassword" type="password" placeholder="Enter your password again" autoComplete="new-password" required minLength={8} />

            <label className="terms-check">
              <input type="checkbox" name="terms" required />
              <span>I agree to the <a href="#terms">Terms of Service</a> and <a href="#privacy">Privacy Policy</a>.</span>
            </label>

            <button className="submit-button" type="submit">Create account <span aria-hidden="true">→</span></button>
            <p className="signin-prompt">Already have an account? <a href="#sign-in">Sign in</a></p>
            {message && <p className="form-message" role="status">{message}</p>}
          </form>
        </div>
      </section>
    </main>
  )
}
