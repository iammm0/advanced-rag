"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import LoadingProgress from "@/components/ui/LoadingProgress";

export default function Home() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    "正在初始化...",
    "正在准备跳转...",
  ];

  useEffect(() => {
    const init = async () => {
      // 步骤1: 检查token
      setCurrentStep(0);
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // 步骤2: 准备跳转
      setCurrentStep(1);
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // 跳转
      router.push("/chat");
    };

    init();
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <LoadingProgress steps={steps} currentStep={currentStep} />
    </div>
  );
}
