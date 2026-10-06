import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home/index.jsx';
import ImageStudio from './pages/ImageStudio/index.jsx';
import Status from './pages/Status/index.jsx';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/images" element={<ImageStudio />} />
        <Route path="/status" element={<Status />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
