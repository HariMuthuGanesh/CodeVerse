document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();

            // Collect user data
            const username = document.getElementById('username').value;
            const rollno = document.getElementById('rollno').value;
            const email = document.getElementById('email').value;

            const userData = {
                username,
                rollno,
                email,
                loginTime: new Date().toISOString()
            };

            // Store in localStorage for persistence across pages
            localStorage.setItem('codeverse_user', JSON.stringify(userData));

            // Send to backend to create session and database entry
            fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // CRITICAL: Phase unlock comes ONLY from backend response (DB-driven)
                        // Do NOT use localStorage for phase completion status
                        console.log('[LOGIN] Phase status from DB:', {
                            phase1_completed: data.phase1_completed,
                            phase2_completed: data.phase2_completed,
                            phase3_completed: data.phase3_completed
                        });

                        // Add a cinematic exit effect
                        const btn = loginForm.querySelector('button[type="submit"]');
                        btn.innerHTML = "ACCESS GRANTED";
                        btn.style.borderColor = "#00ff00";
                        btn.style.boxShadow = "0 0 20px #00ff00";



                        setTimeout(() => {
                            window.location.href = 'phases.html';
                        }, 1000);
                    } else {
                        alert('Login failed: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Login system error. Please try again.');
                });
        });
    }
});
