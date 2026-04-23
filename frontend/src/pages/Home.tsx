import './Home.css'

function Home() {
  return (
    <div className="container">
      <div className="home">
        <h1>Welcome</h1>
        <p>Django + React Full Stack Application</p>
        <div className="stack-info">
          <h2>Tech Stack</h2>
          <ul>
            <li><strong>Backend:</strong> Django + Django REST Framework</li>
            <li><strong>Frontend:</strong> React + Vite + TypeScript</li>
            <li><strong>Database:</strong> PostgreSQL</li>
            <li><strong>API:</strong> REST with CORS enabled</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default Home
