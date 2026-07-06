# GeoAgent Task 82

- 任务编号：82
- LLM：MiniMax-M2.7-highspeed
- 推理配置：thinking 开关未单列记录
- 视觉审查：至少审查一项可视化成果
- 任务难度：advanced

## 任务描述

Link the street view image location points into a path, get the shapefile of the line features. The image was obtained using a mapping vehicle. All points represent the location of a street view image. Each image has an identifier in “panoId” column; the column “link_f_pan” indicates the panoId of the neighbor image in the forward direction, the column “link_b_pan” indicates the panoId of the neighbor image in the backward direction. You can link the location points by: 1) randomly pick up a point; 2) extract its forward and backward neighbors, link them together to form a line segment; 3) find the neighbors of the two ends of the segment, and then link the neighbors to the line segment; 4) repeat step 3, until no more neighbors for the two ends, then start another new path (repeat step 1-4 until all points are processed); 5) ignore points cannot link to others. 6) Make sure that you end up with a shapefile where the line features are stored.
