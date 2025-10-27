<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <div class="error-message">页面未找到</div>
      <div class="error-description">
        抱歉，您访问的页面不存在或已被移除。
      </div>

      <div class="error-actions">
        <el-button type="primary" @click="goHome" size="large">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button @click="goBack" size="large">
          <el-icon><Back /></el-icon>
          返回上一页
        </el-button>
      </div>

      <div class="quick-links">
        <h3>您可能需要：</h3>
        <div class="link-grid">
          <router-link to="/dashboard" class="quick-link">
            <el-icon><DataAnalysis /></el-icon>
            <span>安全仪表板</span>
          </router-link>
          <router-link to="/assets" class="quick-link">
            <el-icon><Box /></el-icon>
            <span>资产管理</span>
          </router-link>
          <router-link to="/vulnerabilities" class="quick-link">
            <el-icon><Warning /></el-icon>
            <span>漏洞管理</span>
          </router-link>
          <router-link to="/tasks" class="quick-link">
            <el-icon><List /></el-icon>
            <span>任务管理</span>
          </router-link>
          <router-link to="/reports" class="quick-link">
            <el-icon><Document /></el-icon>
            <span>报告管理</span>
          </router-link>
          <router-link to="/settings" class="quick-link">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </router-link>
        </div>
      </div>

      <div class="help-section">
        <h3>需要帮助？</h3>
        <p>如果您认为这是一个错误，请联系管理员或查看系统日志。</p>
        <div class="help-actions">
          <el-button type="info" @click="contactSupport">
            <el-icon><Message /></el-icon>
            联系支持
          </el-button>
          <el-button type="info" @click="reportIssue">
            <el-icon><Flag /></el-icon>
            报告问题
          </el-button>
        </div>
      </div>
    </div>

    <!-- Background Animation -->
    <div class="background-animation">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
        <div class="shape shape-6"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}

const contactSupport = () => {
  ElMessage.info('支持功能开发中，请通过邮件联系：support@company.com')
}

const reportIssue = () => {
  ElMessage.info('问题报告功能开发中')
}
</script>

<style scoped lang="scss">
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;

  .not-found-content {
    text-align: center;
    color: white;
    z-index: 10;
    position: relative;
    max-width: 800px;
    width: 100%;

    .error-code {
      font-size: 120px;
      font-weight: 900;
      margin-bottom: 20px;
      background: linear-gradient(45deg, #ff6b6b, #feca57);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      text-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      animation: pulse 2s ease-in-out infinite alternate;
    }

    .error-message {
      font-size: 32px;
      font-weight: 600;
      margin-bottom: 16px;
      text-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }

    .error-description {
      font-size: 18px;
      margin-bottom: 40px;
      opacity: 0.9;
      line-height: 1.6;
    }

    .error-actions {
      display: flex;
      justify-content: center;
      gap: 16px;
      margin-bottom: 60px;
      flex-wrap: wrap;

      .el-button {
        padding: 12px 32px;
        font-size: 16px;
        border-radius: 25px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        }

        &.el-button--primary {
          background: linear-gradient(45deg, #4facfe, #00f2fe);
          border: none;
        }
      }
    }

    .quick-links {
      margin-bottom: 40px;

      h3 {
        font-size: 24px;
        margin-bottom: 24px;
        font-weight: 600;
      }

      .link-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 16px;
        max-width: 600px;
        margin: 0 auto;

        .quick-link {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 20px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          text-decoration: none;
          color: white;
          transition: all 0.3s ease;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);

          &:hover {
            transform: translateY(-4px);
            background: rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
          }

          .el-icon {
            font-size: 32px;
            margin-bottom: 8px;
          }

          span {
            font-size: 14px;
            font-weight: 500;
          }
        }
      }
    }

    .help-section {
      h3 {
        font-size: 20px;
        margin-bottom: 12px;
        font-weight: 600;
      }

      p {
        font-size: 16px;
        opacity: 0.8;
        margin-bottom: 20px;
        line-height: 1.5;
      }

      .help-actions {
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;

        .el-button {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.3);
          color: white;
          border-radius: 20px;

          &:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
          }
        }
      }
    }
  }

  .background-animation {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    z-index: 1;

    .floating-shapes {
      position: relative;
      width: 100%;
      height: 100%;

      .shape {
        position: absolute;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        animation: float 20s infinite linear;

        &.shape-1 {
          width: 80px;
          height: 80px;
          top: 10%;
          left: 10%;
          animation-delay: 0s;
        }

        &.shape-2 {
          width: 120px;
          height: 120px;
          top: 20%;
          right: 10%;
          animation-delay: -5s;
        }

        &.shape-3 {
          width: 60px;
          height: 60px;
          bottom: 30%;
          left: 20%;
          animation-delay: -10s;
        }

        &.shape-4 {
          width: 100px;
          height: 100px;
          bottom: 20%;
          right: 20%;
          animation-delay: -15s;
        }

        &.shape-5 {
          width: 40px;
          height: 40px;
          top: 50%;
          left: 5%;
          animation-delay: -7s;
        }

        &.shape-6 {
          width: 70px;
          height: 70px;
          top: 70%;
          right: 15%;
          animation-delay: -12s;
        }
      }
    }
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  100% {
    transform: scale(1.05);
  }
}

@keyframes float {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) rotate(360deg);
    opacity: 0;
  }
}

@media (max-width: 768px) {
  .not-found {
    padding: 20px 16px;

    .not-found-content {
      .error-code {
        font-size: 80px;
      }

      .error-message {
        font-size: 24px;
      }

      .error-description {
        font-size: 16px;
      }

      .error-actions {
        flex-direction: column;
        align-items: center;

        .el-button {
          width: 100%;
          max-width: 200px;
        }
      }

      .quick-links {
        .link-grid {
          grid-template-columns: repeat(2, 1fr);
        }
      }

      .help-section {
        .help-actions {
          flex-direction: column;
          align-items: center;

          .el-button {
            width: 100%;
            max-width: 180px;
          }
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .not-found {
    .not-found-content {
      .error-code {
        font-size: 60px;
      }

      .error-message {
        font-size: 20px;
      }

      .quick-links {
        .link-grid {
          grid-template-columns: 1fr;
          gap: 12px;
        }
      }
    }
  }
}
</style>