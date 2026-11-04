import { motion, useScroll, useTransform } from "motion/react";

/** Top-right sky glow that fades out on scroll. Animates only opacity and transform. */
export function BlueGlow() {
  const { scrollY } = useScroll();
  const opacity = useTransform(scrollY, [0, 650], [1, 0]);
  const y = useTransform(scrollY, [0, 650], [0, -90]);

  return (
    <motion.div
      aria-hidden
      className="blue-glow pointer-events-none fixed top-0 right-0 -z-10 h-[105vh] w-[90vw] sm:w-[68vw]"
      style={{ opacity, y, willChange: "opacity, transform" }}
    />
  );
}
