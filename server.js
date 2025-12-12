const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const port = 3000;

// استخدم body-parser لتفسير البيانات القادمة من النموذج
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// خدمة الملفات الثابتة مثل HTML و CSS و JavaScript
app.use(express.static('public'));

// نقطة نهاية لاستقبال البلاغ
app.post('/submit-report', (req, res) => {
  const reportData = req.body; // الحصول على البيانات من النموذج
  console.log('Received report:', reportData);

  // هنا يمكنك إضافة الكود لحفظ البيانات في قاعدة بيانات أو ملف JSON
  // في الوقت الحالي سنقوم فقط بطباعة البيانات في الكونسول

  // بعد إرسال البلاغ، سنوجه المستخدم إلى صفحة شكر
  res.redirect('/thank-you.html'); // التوجيه إلى صفحة "تم استلام البلاغ"
});

// بدء الخادم
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
