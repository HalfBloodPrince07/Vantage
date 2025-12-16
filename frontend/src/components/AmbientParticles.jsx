// AmbientParticles.jsx - Subtle floating particles with mouse interaction
import React, { useRef, useEffect, useCallback } from 'react';

const AmbientParticles = ({
    particleCount = 35,
    interactive = true,
    className = ''
}) => {
    const canvasRef = useRef(null);
    const particlesRef = useRef([]);
    const mouseRef = useRef({ x: -1000, y: -1000 });
    const animationRef = useRef(null);

    // Particle class
    class Particle {
        constructor(canvas) {
            this.canvas = canvas;
            this.reset();
        }

        reset() {
            this.x = Math.random() * this.canvas.width;
            this.y = Math.random() * this.canvas.height;
            this.size = Math.random() * 3 + 1;
            this.baseSize = this.size;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            this.opacity = Math.random() * 0.5 + 0.1;
            this.baseOpacity = this.opacity;
            // Subtle color variation
            this.hue = Math.random() > 0.5 ? 190 : 270; // Cyan or violet
        }

        update(mouse) {
            // Gentle drift
            this.x += this.speedX;
            this.y += this.speedY;

            // Mouse interaction - subtle repulsion
            if (mouse.x > 0 && mouse.y > 0) {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const maxDistance = 120;

                if (distance < maxDistance) {
                    const force = (maxDistance - distance) / maxDistance;
                    const angle = Math.atan2(dy, dx);
                    // Push away from mouse
                    this.x -= Math.cos(angle) * force * 2;
                    this.y -= Math.sin(angle) * force * 2;
                    // Increase size and opacity when near mouse
                    this.size = this.baseSize + force * 2;
                    this.opacity = Math.min(this.baseOpacity + force * 0.3, 0.8);
                } else {
                    // Gradually return to base
                    this.size += (this.baseSize - this.size) * 0.05;
                    this.opacity += (this.baseOpacity - this.opacity) * 0.05;
                }
            }

            // Wrap around edges
            if (this.x < -20) this.x = this.canvas.width + 20;
            if (this.x > this.canvas.width + 20) this.x = -20;
            if (this.y < -20) this.y = this.canvas.height + 20;
            if (this.y > this.canvas.height + 20) this.y = -20;
        }

        draw(ctx) {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${this.hue}, 100%, 70%, ${this.opacity})`;
            ctx.fill();

            // Subtle glow
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size * 2, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${this.hue}, 100%, 70%, ${this.opacity * 0.2})`;
            ctx.fill();
        }
    }

    // Initialize particles
    const initParticles = useCallback((canvas) => {
        particlesRef.current = [];
        for (let i = 0; i < particleCount; i++) {
            particlesRef.current.push(new Particle(canvas));
        }
    }, [particleCount]);

    // Animation loop
    const animate = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Update and draw particles
        particlesRef.current.forEach(particle => {
            particle.update(mouseRef.current);
            particle.draw(ctx);
        });

        // Draw connection lines between nearby particles
        particlesRef.current.forEach((p1, i) => {
            particlesRef.current.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 100) {
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(0, 212, 255, ${0.1 * (1 - distance / 100)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            });
        });

        animationRef.current = requestAnimationFrame(animate);
    }, []);

    // Handle resize
    const handleResize = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        initParticles(canvas);
    }, [initParticles]);

    // Handle mouse move
    const handleMouseMove = useCallback((e) => {
        if (interactive) {
            mouseRef.current = { x: e.clientX, y: e.clientY };
        }
    }, [interactive]);

    const handleMouseLeave = useCallback(() => {
        mouseRef.current = { x: -1000, y: -1000 };
    }, []);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // Initial setup
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        initParticles(canvas);
        animate();

        // Event listeners
        window.addEventListener('resize', handleResize);
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseleave', handleMouseLeave);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, [animate, handleResize, handleMouseMove, handleMouseLeave, initParticles]);

    return (
        <canvas
            ref={canvasRef}
            className={`ambient-particles ${className}`}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 0,
                opacity: 0.6
            }}
        />
    );
};

export default AmbientParticles;
