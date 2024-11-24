package edu.berkeley.cs.jqf.fuzz.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class FileUtils {

    private static final Logger logger = LoggerFactory.getLogger(FileUtils.class);

    public static String readFile(String url) {
        FileInputStream fis = null;
        StringBuilder line = new StringBuilder();
        try {
            fis = new FileInputStream(url);
            byte[] data = new byte[1024];
            int bytesRead;
            while ((bytesRead = fis.read(data)) != -1) {
                line.append(new String(data, 0, bytesRead));
            }
        } catch (Exception e) {
            logger.error("Cannot read file: " + url);
            e.printStackTrace();
        } finally {
            try {
                if (fis != null) {
                    fis.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return line.toString();
    }

    public static void writeFile(String url, String content, boolean append) {
        FileOutputStream fos = null;
        try {
            fos = new FileOutputStream(url, append);
            byte[] data = content.getBytes(StandardCharsets.UTF_8);
            fos.write(data);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            try {
                if (fos != null) {
                    fos.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
